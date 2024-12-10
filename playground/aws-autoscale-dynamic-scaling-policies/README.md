### Project Summary

This project sets up AWS Auto Scaling Groups (ASGs) using both Terraform and CloudFormation, focusing on three dynamic scaling policies: simple, step, and target tracking. 

- **Simple Scaling**: Utilizes CloudWatch alarms to scale in and out based on CPU utilization, with a cooldown period to manage rapid scaling.
- **Step Scaling**: Allows for incremental adjustments based on defined CPU thresholds for more nuanced scaling.
- **Target Tracking**: Automatically adjusts capacity to maintain a specified CPU utilization target without manual intervention.

Key parameters include AMI, instance profile, instance type, subnet IDs, and availability zones, all crucial for environment configuration.

For detailed infromation, check out the full article: [Link to Project](https://cloudwith.alon.com.np/blogs/aws-ec2-dynamic-scaling-policies/).