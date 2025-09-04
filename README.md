# 🛠️ Daily AI-Ops Report with AWS Lambda + Bedrock + Teams

This project automates the generation of a **daily AWS operations summary** by:
- Collecting metrics from **CloudWatch**  
- Gathering security findings from **GuardDuty**  
- Fetching cost data from **AWS Cost Explorer**  
- Using **Claude 3 Haiku on Bedrock** to summarize the data  
- Sending the summarized report to **Microsoft Teams** via Webhook  

---

## 🚀 Architecture
1. **EventBridge Rule** triggers the Lambda function (e.g., once per day).  
2. **Lambda**:
   - Fetches CloudWatch metrics (CPU utilization).  
   - Retrieves GuardDuty findings.  
   - Gets cost & usage from Cost Explorer.  
   - Calls **Claude 3 Haiku model on Amazon Bedrock** for AI summarization.  
   - Sends the summarized report to **Teams channel**.  

---

## 📋 Prerequisites
- AWS Account with the following services enabled:
  - **CloudWatch**
  - **GuardDuty**
  - **Cost Explorer**
  - **Bedrock Runtime**
- Microsoft Teams **Incoming Webhook** created and URL available.
- AWS CLI configured with appropriate permissions.

---

## 🔑 Required IAM Permissions
Attach an IAM role to the Lambda with the following policies (or equivalent custom policy):
- `AmazonBedrockFullAccess` (for Bedrock Runtime)
- `CloudWatchReadOnlyAccess`
- `AmazonGuardDutyReadOnlyAccess`
- `AWSBillingConductorServicePolicy` (or Cost Explorer read permissions)
- `AWSLambdaBasicExecutionRole`

---

## ⚙️ Environment Variables
Set these environment variables in your Lambda configuration:

| Variable             | Description                                                                 | Example Value                                  |
|----------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| `TEAMS_WEBHOOK_URL`  | MS Teams incoming webhook URL                                               | `https://outlook.office.com/webhook/...`      |
| `BEDROCK_MODEL_ID`   | Bedrock model ID (Claude 3 Haiku recommended)                               | `anthropic.claude-3-haiku-20240307-v1:0`      |

---

## 🧑‍💻 Deployment
1. Clone the repository and package the Lambda function:
   ```bash
   zip -r lambda_package.zip lambda_function.py
