import boto3
import argparse
import time
from datetime import timedelta, date, datetime
from botocore.config import Config

# Create an argument parser to accept input parameters
parser = argparse.ArgumentParser()
# Add arguments for source AMI, source account, destination account, and email recipient
parser.add_argument('-a', '--sourceAMI', type=str, help='SourceAMI')
parser.add_argument('-s', '--sourceAccount', type=str, help='SourceAccount')
parser.add_argument('-d', '--destinationAccount', type=str, help='DestinationAccount')
parser.add_argument('-e', '--email', type=str, help='EmailRecipient')

args = parser.parse_args()

srcAMIId = args.sourceAMI
srcAccountName = args.sourceAccount
destAccountName = args.destinationAccount
emailRecipient = args.email

todayDate = date.today()

accountConfig = {
    "AccountA": {"id": "123123123123"},
    "AccountB": {"id": "321321312321"},
}

# Define the KMS key alias to use for encrypting the copied AMI
ebsKMSKeyForShareAMI = "alias/kms-custom-key"

# Function to get a session for a given AWS account
def getSession(accountId, service, sessionType, region='us-east-1'):
    sts_client = boto3.client('sts')

    retryConfig = Config(
        retries=dict(
            max_attempts=10
        )
    )
    session = ""
    iamRoleArn = 'arn:aws:iam::' + accountId + ':role/role_sts_cross_account'
    sts_response = sts_client.assume_role(
        RoleArn=iamRoleArn,
        RoleSessionName='sts-share-ami-operation',
    )
    if sessionType == "client":
        session = boto3.client(service, aws_access_key_id=sts_response['Credentials']['AccessKeyId'],
                               aws_secret_access_key=sts_response['Credentials']['SecretAccessKey'],
                               aws_session_token=sts_response['Credentials'][
                                   'SessionToken'],
                               region_name=region,
                               config=retryConfig
                               )
    elif sessionType == "resource":
        session = boto3.resource(service,
                                 aws_access_key_id=sts_response['Credentials']['AccessKeyId'],
                                 aws_secret_access_key=sts_response['Credentials']['SecretAccessKey'],
                                 aws_session_token=sts_response['Credentials'][
                                     'SessionToken'],
                                 region_name=region,
                                 config=retryConfig)

    return session

# Function to send email notifications (using SES)
def sendEmail(recipient, subject, message):
    try:
        destination = {
            'ToAddresses': [recipient],
        }
        print(f"Email '{subject}' Initiated To: {recipient}")

        ses = boto3.client('ses', region_name='us-east-1')
        response = ses.send_email(
            Source='Admin <admin@example.com>',
            Destination=destination,
            Message={'Subject': {'Data': subject}, 'Body': {'Html': {'Data': message, 'Charset': 'UTF-8'}}}
         )
        print("Email Success!!")
    except Exception as e:
        print(f"Email Failed!! Error: {e}")

# Function to add tags to AMIs
def ec2AddTags(ec2Client, resourceId, tagList):
    try:
        # Create tags on the specified resources
        tagResponse = ec2Client.create_tags(Resources=[resourceId], Tags=tagList)
        print(f"ec2AddTags() INFO : Tags Added to {resourceId}")
    except Exception as e:
        print(f"ec2AddTags() ERROR: {e}")

def addTags(ec2Client, amiId, snapList, tagList):
    ec2AddTags(ec2Client, amiId, tagList)
    for snapId in snapList:
        ec2AddTags(ec2Client, snapId, tagList)

def getAMITagInfo(amiMetadata):
    try:
        for ami in amiMetadata['Images']:
            amiDescription = f"CopyAMI_Source_{srcAccountName}_{srcAMIId}_{ami['Description']}_{todayDate}_Automated" if \
            ami[
                'Description'] else f"CopyAMI_Source_{srcAMIId}_{todayDate}_Automated"
            tagList = ami['Tags'] if ami['Tags'] else []
            amiName = ami['Name']
            print(f"AMIName: {amiName}, AMIDescription: {amiDescription}, AMITagList: {tagList}")
            return amiName, amiDescription, tagList
    except Exception as e:
        print(f"getAMITagInfo() Error:{e}")
        return "TagError", "TagError", [{'Key': 'Name', 'Value': 'TagError'}]


def removeAMISnapShot(ec2Client, amiId, SnapList):
    try:
        amiResponse = ec2Client.deregister_image(
            ImageId=amiId,
        )
        print(f"removeAMISnapShot() INFO : Removed AMI: {amiId} Log: {amiResponse}")

        for snap in SnapList:
            snapResponse = ec2Client.delete_snapshot(
                SnapshotId=snap,
            )
            print(f"removeAMISnapShot() INFO : Removed Snap: {snap} Log: {snapResponse}")
    except Exception as e:
        print(f"removeAMISnapShot() ERROR: Error while removing AMI {amiId} and SnapList: {SnapList}. Log: {e}")

# Function to deregister an AMI and delete its snapshots after success copy
def getAMIMetadata(ec2Client, amiId, accountId):
    try:
        amiResponse = ec2Client.describe_images(
            ImageIds=[
                amiId,
            ],
            Owners=[
                accountId,
            ]
        )
        return amiResponse
    except Exception as e:
        raise Exception(f"getAMIMetadata() ERROR: {e}")


def getAMIsSnapsList(ec2Client, amiId, accountId):
    amiSnapList = []
    try:
        amiResponse = ec2Client.describe_images(
            ImageIds=[
                amiId,
            ],
            Owners=[
                accountId,
            ],
        )
        for ami in amiResponse['Images']:
            for snap in ami['BlockDeviceMappings']:
                if 'Ebs' in snap:
                    amiSnapList.append(snap['Ebs']['SnapshotId'])
        return amiSnapList
    except Exception as e:
        raise Exception(f"getAMISnapsList() ERROR: {e}")

# Function to copy an AMI with encryption and a custom KMS key
def copyAMIWithEncryption(ec2Client, amiId, accountId, amiName, amiDescription, kmsKey='alias/aws/ebs'):
    try:
        copyAMIResponse = ec2Client.copy_image(
            Description=amiDescription,
            Encrypted=True,
            KmsKeyId=kmsKey,
            Name=amiName,
            SourceImageId=amiId,
            SourceRegion='us-east-1'
        )
        print(f"copyAMIWithEncryption() INFO : AMI: {copyAMIResponse['ImageId']} AccountId: {accountId}")
        while True:
            amiMetadata = getAMIMetadata(ec2Client, copyAMIResponse['ImageId'], accountId)
            for ami in amiMetadata['Images']:
                if ami['State'] == "available":
                    return copyAMIResponse['ImageId']
                else:
                    print(
                        f"copyAMIWithEncryption() INFO: AMI: {copyAMIResponse['ImageId']} State: {ami['State']}. "
                        f"Re-trying after 10sec.")
                    time.sleep(10)
                    continue
    except Exception as e:
        raise Exception(f"copyAMIWithEncryption() Exception : {e}, AMI: {amiId}, AccountId: {accountId}")


# Function to share an AMI with another AWS account by modifying the AMI's permissions
def shareAMI(srcEncryptedAMI, srcEc2Client, snapList, destAccountId):
    try:
        def grantAddVolumePermission():
            for snapId in snapList:
                snapsMetaData = srcEc2Client.modify_snapshot_attribute(
                    SnapshotId=snapId,
                    CreateVolumePermission={
                        'Add': [
                            {
                                'UserId': destAccountId
                            }
                        ]
                    }
                )
                print(f"shareAMI() INFO: CreateVolume Permission added on SnapShot: {snapId}")

        modifyAMIResponse = srcEc2Client.modify_image_attribute(
            Attribute='launchPermission',
            ImageId=srcEncryptedAMI,
            LaunchPermission={
                'Add': [
                    {
                        'UserId': destAccountId,
                    },
                ]
            },
            OperationType='add',
        )
        print(f"shareAMI() INFO: Share Permission added on AMI: {srcEncryptedAMI}")
        grantAddVolumePermission()
    except Exception as e:
        raise Exception(f"shareAMI() ERROR : {e}")

def main():
    print(f"##Action -> Copy AMI: {srcAMIId} Source Account: {srcAccountName} Destination Account: {destAccountName}")
    srcAccountId = accountConfig[srcAccountName]['id']
    destAccountId = accountConfig[destAccountName]['id']
    srcEc2Client = getSession(srcAccountId, "ec2", "client")
    destEc2Client = getSession(destAccountId, "ec2", "client")
    # Get AMI Details -> Tags, Name and Description
    amiMetadata = getAMIMetadata(srcEc2Client, srcAMIId, srcAccountId)
    amiName, amiDescription, amiTagList = getAMITagInfo(amiMetadata)
    # Copy AMI with Custom Encryption Key and Get its SnapShot
    srcEncryptedAMI = copyAMIWithEncryption(srcEc2Client, srcAMIId, srcAccountId, amiName, amiDescription,
                                            ebsKMSKeyForShareAMI)
    srcEncryptedAMISnapsList = getAMIsSnapsList(srcEc2Client, srcEncryptedAMI, srcAccountId)
    # Add Tags
    addTags(srcEc2Client, srcEncryptedAMI, srcEncryptedAMISnapsList, amiTagList)
    # Share AMI To Destination Account
    shareAMI(srcEncryptedAMI, srcEc2Client, srcEncryptedAMISnapsList, destAccountId)
    # Copy the shared AMI and Own it in Destination Account
    destFinalAMIId = copyAMIWithEncryption(destEc2Client, srcEncryptedAMI, destAccountId, amiName, amiDescription)
    destFinalAMISnapsList = getAMIsSnapsList(destEc2Client, destFinalAMIId, destAccountId)
    # Add Tags in Destination AMI and Snapshots
    addTags(destEc2Client, destFinalAMIId, destFinalAMISnapsList, amiTagList)
    print(f"main () INFO : Destination AMI: {destFinalAMIId} SnapList: {destFinalAMISnapsList}")
    # Delete Shared AMI and it's Snap
    removeAMISnapShot(srcEc2Client, srcEncryptedAMI, srcEncryptedAMISnapsList)
    print(
        f"main () INFO : Shared AMI: {srcEncryptedAMI} SnapList: {srcEncryptedAMISnapsList} "
        f"Deleted from Source Account : {srcAccountName}")

    # Notification
    subject = f"AWS AMI Migration Details: {str(todayDate)}"
    bodyMessage = (f"[SourceAccount: {srcAccountName}, SourceAMI: {srcAMIId}, DestinationAccount: {destAccountName}, "
                   f"DestinationAMI: {destFinalAMIId}, KMSKey: {ebsKMSKeyForShareAMI}]")
    sendEmail(emailRecipient, subject, bodyMessage)


if __name__ == "__main__":
    main()
