## Overview:

Securely sharing files over SFTP, FTP, and FTPS is a staple within many business-to-business (B2B)
workflows. Across industries, companies use this mechanism to report inventory, invoice, and
compliance information. AWS's framework for protecting against ransomware events includes
continuous monitoring to detect and respond to security findings for your workloads. For your file
transfer workloads, you can scan each file you receive, and isolate malicious files before they ever reach
your downstream systems. New files only reach your systems after an automated vetting process runs a
series of security tooling, like antivirus checks.

## Deploying the solution:

Deploying the AWS CloudFormation templates that create the following resources: 
- Amazon S3 bucket
- AWS Transfer Family server
- AWS Lambda functions
- AWS Secrets Manager secrets
- AWS CodeBuild project
- Amazon ECR repository
- Amazon EventBridge rules
- IAM Roles and Policies

#### Cloudformation
To deploy the CloudFormation template, follow these steps:
1. Open AWS CloudShell in your AWS account
2. Clone this post’s GitHub repository using git clone command (git clone https://github.com/aws-samples/transfer-family-anti-virus-cdk.git)
3. Change into the transfer-family-anti-virus-cdk directory (cd transfer-family-anti-virus-cdk)
4. Provide executable permissions to deployStack.sh bash script (chmod +x deployStack.sh)
5. Run the deployStack bash script to create the required resources (./deployStack.sh)
6. Copy the SFTPEndpoint, User name and password to use later. SFTPEndpoint is the fully qualified domain name of your Transfer Family server.
    
The script takes less than 20 minutes to run and change to a CREATE_COMPLETE state. If you deploy the stack twice in the same AWS account and Region, some resources may already exists and the process fails with a message indicating the resource already exists in another template.

#### CDK
Users can also make use of CDK to deploy the solution by following the steps below.
 1.	Configure the aws credentials
 2.	Change into the transfer-family-anti-virus-cdk directory
 3.	Create a virtual env (virtualenv .env)
 4.	Activate the virtual environment (source .env/bin/activate)
 5.	Install the necessary dependencies (pip install -r images/cdk-deploy/requirements.txt)
 6.	Bootstrap the CDK environment (cdk bootstrap aws://$ACCOUNT_ID/$AWS_REGION)
 7.  Deploy the solution (cdk deploy -a ./app.py)


