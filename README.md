# Guidance for detecting malware threats using AWS Transfer Family managed workflows

## Table of Contents
1. [Introduction](#introduction)
2. [Malware threats in file transfers](#malware-threats-in-file-transfers)
3. [Core Concepts](#core-concepts)
4. [Solution Overview](#solution-overview)
5. [Costs and licenses](#costs-and-licenses)
6. [Deployment options](#deployment-options)
7. [Deployment steps](#deployment-steps)
8. [Post deployment steps](#post-deployment-steps)
9. [Additional information](#additional-information)
10. [Troubleshooting](#troubleshooting)
11. [Resources](#resources)
12. [Customer responsibility](#customer-responsibility)
13. [Feedback](#feedback)
14. [Notices](#notices)

---

<a name="introduction"></a>
## Introduction

This user guide is created for anyone who is interested in detecting malware threats using [AWS Transfer Family](https://aws.amazon.com/aws-transfer-family/) as it is a popular choice for secure file transfer tailor-made for [Amazon Simple Storage Service (Amazon S3)](https://aws.amazon.com/s3/) and [Amazon Elastic File System (Amazon EFS)](https://aws.amazon.com/efs/).

[Transfer Family managed workflows](https://docs.aws.amazon.com/transfer/latest/userguide/transfer-workflows.html) empower you to process files through preset actions, including copying, tagging, decrypting, and even custom preprocessing via AWS Lambda. This offers flexibility, allowing you to integrate your specific code for tasks like malicious content detection, PII obfuscation, data encryption, and alert generation. Upon file upload completion, Transfer Family's managed workflows initiate automatically, forwarding logs to Amazon CloudWatch.

This guide provides the steps to set up a workflow that leverages [Clam Antivirus (ClamAV)](https://www.clamav.net/) — a renowned open-source antivirus engine proficient in detecting a myriad of threats such as trojans, malware, and viruses with periodic updates to virus definitions to remain abreast of emerging threats.

Following this guide, you should be able to:
- Familiarize with managed workflow on AWS Transfer Family to detect the malware.
- Learn ways to detect those threats and quarantine using antivirus.
- Deploy ClamAV with AWS Lambda and continuously update ClamAV virus definitions.


---
<a name="malware-threats-in-file-transfers"></a>
## Malware threats in file transfers
The reliable transfer of files via SFTP, FTP, and FTPS remains foundational in many business-to-business (B2B) operations. Across various sectors, businesses rely on file transfers to relay information such as inventory, invoicing, and compliance data. There may be presence of malicious content in these files which can create financial repercussions and damage to the brand image.

You can deploy the malware detection in the context of file transfers, so that you can screen every incoming file, separating any harmful content before it infiltrates the main systems. Only after a comprehensive security verification, encompassing tools like antivirus scans, should new files be integrated into your systems.

<a name="core-concepts"></a>
## Core Concepts
Below is a high-level overview of the Core Concepts that are incorporated into malware threats detection in AWS Transfer Family. We will assume the reader is familiar with Git, Python, and AWS.

| Concept | Description |
|---------|-------------|
| [AWS Transfer Family](https://aws.amazon.com/aws-transfer-family/faqs/) | Seamlessly migrate, automate, and monitor your file transfer workflows into and out of Amazon S3 and Amazon EFS. |
| [Custom Authentication](https://aws.amazon.com/secrets-manager/) | Authentication through keys stored in secret manager. |
| Virus Definitions | Information about known viruses and malware signatures. |
| [AWS CodeBuild](https://aws.amazon.com/codebuild/) | Fully Managed continuous integration service that compiles source code, runs tests, and produces software packages that are ready to deploy. |
| [TF Managed Workflows](https://docs.aws.amazon.com/transfer/latest/userguide/transfer-workflows.html) | A feature within AWS Transfer Family enabling automated processing of files through predefined actions such as copying, tagging, and decrypting, facilitated by AWS Lambda for custom preprocessing tasks. |
| [AWS Lambda](https://aws.amazon.com/lambda/) | Serverless compute service that runs code in response to events and automatically manages the compute resources, enabling developers to build applications that scale with business needs. |
| [Amazon EventBridge Scheduler](https://aws.amazon.com/eventbridge/scheduler/) | Serverless scheduler that enables you to schedule tasks and events at scale. |

---

<a name="solution-overview"></a>
## Solution Overview
This design blueprint outlines the setup of a Transfer Family server integrated with a managed workflow that employs ClamAV for scanning every file upon upload. While this particular server utilizes the SFTP protocol to relay files to Amazon S3, it's worth noting that the workflows are adaptable and can support SFTP, FTPS, and FTP protocols within Transfer Family servers, and they can facilitate transfers to Amazon EFS as well. The example here focuses on file transfers directed towards Amazon S3 and incorporates a workflow tailored for real-time file scanning. Moreover, it's feasible to integrate the ClamAV scanning phase into existing workflows. A practical application could be decrypting the file initially, followed by a ClamAV scan. An added advantage of this blueprint is its provision for automatic updates of both the ClamAV codebase and its virus definitions, ensuring the scanning mechanism remains contemporary without necessitating manual intervention. The subsequent illustration delineates the sequence of operations required to authenticate the Transfer Family server, initiate a file upload, trigger the managed workflow, and consistently refresh the virus definitions.

---

<a name="costs-and-licenses"></a>
## Costs and Licenses
While utilizing this solution doesn't incur any direct charges, please be aware that you will incur costs for the AWS services or resources activated by this solution architecture.

![Architecture Diagram](./images/Picture1.png)

Figure 1. Detect malware threats using AWS Transfer Family - Architecture


1. User sends an authentication request to the AWS Transfer Family server which forwards the request to authenticate the user using a custom identity provider.
2. AWS Transfer Family sends user credentials, protocol, and IP address to AWS Lambda Function, using SSH key-based authentication if no password is provided.
3. AWS Lambda function sends query to AWS Secret manager for authentication.
4. AWS Secrets Manager provides user credentials, including stored password, IAM role mapping, SSH key data, source IP CIDRs and directory mappings.
5. The Lambda function verifies the login and sends user-specific configurations to AWS Transfer Family.
6. The user uploads the files to the AWS Transfer Family server. Each file is put into an Amazon S3 bucket and invokes a distinct workflow execution.
7. The AWS Transfer Family managed workflow initializes a sequence of processing steps configured. In the workflow step, the AWS Lambda function scans each file with a ClamAV installed container image.
8. Based on the scan result from the AWS Lambda function, the managed workflow tags the files appropriately either as INFECTED or CLEAN
9. An AWS EventBridge Scheduler rule is configured to run based on a cron expression to update the ClamAV image and virus definition.
10. AWS CodeBuild builds the container image, adds the latest ClamAV virus definitions and uploads to Amazon ECR.
11. The AWS Lambda function pulls the built container image from Amazon ECR and updates the AWS Lambda function as part of the managed workflow.


The solution encompasses several intertwined components, with the Transfer Family's managed workflow involving numerous stages, such as custom Lambda functions and tagging, all triggered by a singular event. Should there be alterations in the state during any of these stages, it necessitates corresponding adjustments in the following steps. To illustrate, if there's a customized procedure that decompresses a file and redirects it to a fresh Amazon S3 prefix, it's imperative to reconfigure the ClamAV image to reference the updated path.

---

<a name="deployment-options"></a>
## Deployment Options

This solution provides the following deployment options:

- [Deploy using a shell script running CloudFormation templates](https://github.com/aws-solutions-library-samples/transfer-family-anti-virus-cdk/blob/main/deployStack.sh)
- [Deploy using CDK](https://github.com/aws-solutions-library-samples/transfer-family-anti-virus-cdk)

---

<a name="deployment-steps"></a>
## Deployment Steps

1. **Open AWS CloudShell in your AWS account.**
2. **Clone this post’s GitHub repository using the git clone command:**
git clone https://github.com/aws-solutions-library-samples/guidance-for-detecting-malware-threats-using-aws-transfer-family-managed-workflows.git
![Figure 2: Screenshot of git clone command in AWS CloudShell](./images/Picture2.png)

Figure 2: Screenshot of git clone command in AWS CloudShell
3. **Change the directory into the “transfer-family-anti-virus-cdk” folder:**

    `cd transfer-family-anti-virus-cdk`

4. **Provide executable permissions to deployStack.sh bash script:**

    `chmod +x deployStack.sh`

5. **Run the deployStack bash script with the USER_NAME as an argument to create the required resources:**

    `./deployStack.sh $USER_NAME`

    ![Figure 4: Screenshot showing the SFTP endpoint output](./images/Picture3.png)

   Figure 3: Screenshot of running the deployStack script

6. **Copy the SFTPEndpoint from the output and note the username from the previous step to use later. SFTPEndpoint is the fully qualified domain name of your Transfer Family server.**
![Figure 5: Screenshot showing the username and generated password for use](./images/Picture4.png)

   Figure 4: Screenshot showing the SFTP endpoint output

7. **Retrieve the password generated and stored in the AWS Secrets Manager secret named SFTP/USERNAME to use later.**
![Figure 6: Screenshot showing the SFTP endpoint output](./images/Picture5.png)

   Figure 5: Screenshot showing the username and generated password for use.


The script takes less than 20 minutes to run and create the necessary resources for the solution.

---
<a name="post-deployment-steps"></a>
## Post Deployment Steps

You can test the end-to-end configuration by following these steps:

1. **Uploading a clean file through the SFTP endpoint, user name, and password from Steps 6 and 7 in the ‘Deploying the solution’ section.**

2. **The managed transfer workflow is executed in a few seconds, and the S3 object in the ClamAV-scan-landing zone-* bucket is tagged as CLEAN. It's now accessible for download**
   ![Figure 6: Screen capture of the Amazon S3 Object tag for a clean file](./images/Picture6.png)

   Figure 6: Screen capture of the Amazon S3 Object tag for a clean file


3. **Download an anti-malware test file from eicar.org, a test file developed by the European Institute for Compute Anti-virus Research. Note that you must adhere to your organization’s information security best practices and guidelines. Make sure you carefully read and understand the terms of use for the test file before downloading.**

4. **Upload the anti-malware test file through the SFTP endpoint, user name, and password from Steps 6 and 7 in the ‘Deploying the solution’ section.**

5. **The managed transfer workflow is executed, and custom preprocessing using Lambda function scans the uploaded file for malware.**
   ![Figure 7: Screen capture of the CloudWatch Logs for an infected file](./images/Picture7.png)

   Figure 7: Screen capture of the CloudWatch Logs for an infected file

6. **The Amazon S3 object in clamav-scan-landingzone-* bucket is tagged as INFECTED. The file is not available for download, as the solution denies the download of infected objects.**
   ![Figure 8: Screen capture of the Amazon S3 Object tag for an infected file](./images/Picture8.png)

   Figure 8: Screen capture of the Amazon S3 Object tag for an infected file

7. **(Optional) Edit the EventBridge rule (clamav-codebuild-cronEventRule-*) configured to refresh the ClamAV code and virus definitions. Note that you should troubleshoot and monitor any issues using the logs generated in CloudWatch.**
   ![Figure 9: Screen capture of editing an EventBridge scheduled standard rule](./images/Picture9.png)

   Figure 9: Screen capture of editing an EventBridge scheduled standard rule

---
<a name="additional-information"></a>
## Additional Information

**Troubleshoot and monitor any issues using the logs generated in Amazon CloudWatch.**
![Figure 10: Screen capture indicating the various log groups generated by the solution](./images/Picture10.png)

Figure 10: Screen capture indicating the various log groups generated by the solution

---
<a name="troubleshooting"></a>
## Troubleshooting

For troubleshooting common issues, refer to the [Troubleshooting CDK](https://docs.aws.amazon.com/cdk/v2/guide/troubleshooting.html) and [Troubleshooting CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/troubleshooting.html).

---
<a name="resources"></a>
## Resources
- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS Transfer Family Managed Workflows](https://aws.amazon.com/aws-transfer-family/)
- [AWS Transfer Family managed workflows](https://docs.aws.amazon.com/transfer/latest/userguide/transfer-workflows.html)

---
<a name="customer-responsibility"></a>
## Customer Responsibility
Upon deploying the solution, ensure that all your resources and services are up-to-date and appropriately configured. This includes the application of necessary patches to align with your security requirements and other specifications. For a comprehensive understanding of the roles and responsibilities in maintaining security, please consult the Shared Responsibility Model.

---
<a name="feedback"></a>
## Feedback

To submit feature ideas and report bugs, use the Issues section of the [GitHub repository](https://github.com/aws-solutions-library-samples/guidance-for-detecting-malware-threats-using-aws-transfer-family-managed-workflows) for this Partner Solution. To submit feedback on this deployment guide, use the following GitHub links: [Issues](https://github.com/aws-solutions-library-samples/guidance-for-detecting-malware-threats-using-aws-transfer-family-managed-workflows/issues).

---
<a name="notices"></a>
## Notices

This document is provided for informational purposes only. It represents current AWS product offerings and practices as of the date of issue of this document, which are subject to change without notice. Customers are responsible for making their own independent assessment of the information in this document and any use of AWS products or services, each of which is provided "as is" without warranty of any kind, whether expressed or implied. This document does not create any warranties, representations, contractual commitments, conditions, or assurances from AWS, its affiliates, suppliers, or licensors. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers.

The software included with this paper is licensed under the Apache License, version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at [https://aws.amazon.com/apache2.0/](https://aws.amazon.com/apache2.0/) or in the accompanying "license" file. This code is distributed on an "as is" basis, without warranties or conditions of any kind, either expressed or implied. Refer to the License for specific language governing permissions and limitations.

---
