import os
import json
import boto3
import urllib3
from datetime import datetime, timedelta

# --- ENV VARIABLES ---
TEAMS_WEBHOOK_URL = os.environ["TEAMS_WEBHOOK_URL"]
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")

# --- AWS Clients ---
cloudwatch = boto3.client("cloudwatch")
guardduty = boto3.client("guardduty")
ce = boto3.client("ce")
bedrock = boto3.client("bedrock-runtime")

http = urllib3.PoolManager()


def get_cloudwatch_metrics():
    """Fetch sample CPU utilization metric for last 24h"""
    end = datetime.utcnow()
    start = end - timedelta(hours=24)

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": "i-02bff645f777c0da4"}],  # Replace with real EC2 ID
        StartTime=start,
        EndTime=end,
        Period=3600,
        Statistics=["Average"]
    )
    return response.get("Datapoints", [])


def get_guardduty_findings():
    """Get sample GuardDuty findings"""
    detectors = guardduty.list_detectors()["DetectorIds"]
    if not detectors:
        return []
    findings = guardduty.list_findings(DetectorId=detectors[0], MaxResults=5)
    if not findings["FindingIds"]:
        return []
    details = guardduty.get_findings(
        DetectorId=detectors[0], FindingIds=findings["FindingIds"]
    )
    return details["Findings"]


def get_cost_report():
    """Get yesterday's AWS cost"""
    end = datetime.utcnow().date()
    start = end - timedelta(days=1)

    result = ce.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(end)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )
    return result["ResultsByTime"]


def summarize_with_bedrock(data_dict):
    """Send collected data to Claude 3 Haiku for summarization"""

    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    prompt = f"""
    You are an AI Ops assistant. Summarize the following AWS operational data into a 
    concise daily report with categories: Infra Health, Security, Cost, and Recommendations.

    Data: {json.dumps(data_dict, indent=2, default=default_serializer)}
    """

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.7,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
    })

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,  # anthropic.claude-3-haiku-20240307-v1:0
        body=body,
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    outputs = result.get("content", [])
    if outputs and "text" in outputs[0]:
        return outputs[0]["text"]
    return "Summary unavailable"


def post_to_teams(summary):
    """Send summarized report to Teams channel via Webhook"""
    message = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": "Daily AI-Ops Report",
        "sections": [{
            "activityTitle": f"📊 Daily AI-Ops Report – {datetime.utcnow().strftime('%Y-%m-%d')}",
            "text": summary
        }]
    }

    encoded_msg = json.dumps(message).encode("utf-8")
    response = http.request(
        "POST",
        TEAMS_WEBHOOK_URL,
        body=encoded_msg,
        headers={"Content-Type": "application/json"}
    )
    print("Teams response:", response.status)


def lambda_handler(event, context):
    # Step 1: Gather data
    metrics = get_cloudwatch_metrics()
    security = get_guardduty_findings()
    cost = get_cost_report()

    # Step 2: Summarize with AI
    summary = summarize_with_bedrock({
        "cloudwatch": metrics,
        "guardduty": security,
        "cost": cost
    })

    # Step 3: Post to Teams
    post_to_teams(summary)

    return {"status": "Report sent to Teams"}
