This Python script automates copying an AMI from one AWS account to another, ensuring the AMI is encrypted with a custom KMS key. It requires proper permissions, role assumptions, and KMS key configuration for both the source and destination accounts.

A complete blog post on this process can be found [here](https://cloudwith.alon.com.np/blogs/share-ami-securely-across-aws-account/).

### **Pre-requisites:**

1. **Required Access:**  
   Ensure both source and destination AWS accounts have the necessary permissions for the operations (role assumption, AMI copying, modifying permissions, etc.).

2. **Custom KMS Key:**  
   The script uses a custom KMS key for encryption. Set the KMS key alias in the `ebsKMSKeyForShareAMI` variable.

3. **Role Assumption:**  
   Create an IAM role `role/role_sts_cross_account` in both the source and destination accounts to allow role assumption for the script to perform necessary operations.

### **Installation:**
1. **Install the required dependencies:** 

    The script requires several Python libraries. Install them using pip:

    ```bash
    pip install -r requirement.txt
    ```
    The requirements.txt file includes the necessary libraries for interacting with AWS services and handling permissions.   

### **Step-by-Step Workflow:**

1. **Update the `accountConfig` Dictionary:**  
   Define the AWS account IDs for both the source and destination accounts.
   ```python
   accountConfig = {
       "AccountA": {"id": "123123123123"},
       "AccountB": {"id": "321321312321"},
   }
   ```

2. **Set the Custom KMS Key:**  
   Update the custom KMS key in the `ebsKMSKeyForShareAMI` variable for AMI encryption.
   ```python
   ebsKMSKeyForShareAMI = "alias/your-custom-kms-key"
   ```

3. **Run the Script with Parameters:**  
   Execute the script with the following parameters:
   ```bash
   python3 main.py -s AccountA -d AccountB -a ami-xxxid -e email@example.com
   ```
   - `-s`: Source account name (e.g., `AccountA`).
   - `-d`: Destination account name (e.g., `AccountB`).
   - `-a`: AMI ID to copy (e.g., `ami-xxxid`).
   - `-e`: Email address for notifications (e.g., `email@example.com`).

4. **Role Assumption for Source Account:**  
   The script assumes the role in the source account using AWS STS.

5. **AMI Copy (us-east-1 only):**  
   The script copies the AMI within the same region (`us-east-1` by default), encrypting it with the custom KMS key.

6. **Check AMI Status:**  
   The script checks the status of the copied AMI every 10 seconds. Once available, it proceeds to share the AMI.

7. **Share AMI with Destination Account:**  
   The AMI is shared with the destination account, granting read permissions for the AMI and its snapshots.

8. **Role Assumption for Destination Account:**  
   After sharing, the script assumes the role in the destination account.

9. **Copy Shared AMI to Destination Account:**  
   The script copies the shared AMI to the destination account, making it the owner of the AMI.

10. **Re-check AMI Status:**  
    The script checks the status of the AMI in the destination account every 10 seconds. Once available, it proceeds to clean up.

11. **Clean Up in Source Account:**  
    After the AMI is copied successfully in the destination account, the script deletes the shared AMI and snapshots from the source account.

12. **Send Email Notification:**  
    The script sends an email via AWS SES to the specified recipient with details of the operation, including:
    - Source account and AMI ID
    - Destination account and AMI ID
    - KMS key used for encryption

### **Key Considerations:**

- **Region Limitation:**  
   The script currently supports only the `us-east-1` region. Modify the script to support additional regions if needed.

- **Permissions:**  
   Ensure both accounts have the required permissions for assuming roles, copying AMIs, modifying permissions, and deleting snapshots.

- **Custom KMS Key Access:**  
   The destination account must have access to the custom KMS key. Ensure the KMS key policy grants permissions to the destination account.