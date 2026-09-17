"""
Serverless Feedback & Contact Form — Lambda Function
=====================================================

Routes:
  POST /feedback -> Save message to DynamoDB + notify via SNS
  GET  /stats    -> Return total message count

API Gateway: HTTP API, payload format version 2.0

Environment variables (set these in Lambda -> Configuration -> Environment variables):
  TABLE_NAME = FeedbackMessages
  TOPIC_ARN  = <fill in once you create the SNS topic in Phase 6>
"""

import json
import os
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

TABLE_NAME = os.environ["TABLE_NAME"]
TOPIC_ARN = os.environ["TOPIC_ARN"]

table = dynamodb.Table(TABLE_NAME)

# Update this if your CloudFront domain ever changes
ALLOWED_ORIGIN = "https://dg6yygcvdtl2c.cloudfront.net"


def lambda_handler(event, context):
    route = event.get("routeKey", "")
    print(f"Route: {route}")

    if route == "POST /feedback":
        return handle_submit(event)
    if route == "GET /stats":
        return handle_stats()

    return _response(404, {"error": "Endpoint not found", "route": route})


def handle_submit(event):
    try:
        raw_body = event.get("body", "{}")
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body

        required = ["name", "email", "subject", "message"]
        missing = [f for f in required if not str(body.get(f, "")).strip()]
        if missing:
            return _response(400, {"error": "Missing required fields: " + ", ".join(missing)})

        # "id" must match your table's partition key exactly
        record = {
            "id": str(uuid.uuid4()),
            "name": body["name"].strip(),
            "email": body["email"].strip(),
            "subject": body["subject"].strip(),
            "category": body.get("category", "general"),
            "message": body["message"].strip(),
            "status": "new",
            "created_at": datetime.utcnow().isoformat(),
        }

        table.put_item(Item=record)

        # Don't let an SNS failure break a successful save
        try:
            _send_notification(record)
        except Exception as sns_err:
            print(f"SNS publish failed (feedback was still saved): {sns_err}")

        return _response(200, {
            "message_id": record["id"],
            "message": "Your message has been sent successfully!"
        })

    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON request body."})
    except Exception as e:
        print(f"Error in handle_submit: {e}")
        return _response(500, {"error": "Internal server error. Please try again."})


def handle_stats():
    try:
        result = table.scan(Select="COUNT")
        return _response(200, {"total_messages": result.get("Count", 0)})
    except Exception as e:
        print(f"Error in handle_stats: {e}")
        return _response(500, {"error": str(e)})


def _send_notification(record):
    subject = f"[FeedbackHub] New message: {record['subject']}"
    message_body = (
        f"New message received on FeedbackHub\n\n"
        f"From: {record['name']} <{record['email']}>\n"
        f"Category: {record['category']}\n"
        f"Subject: {record['subject']}\n\n"
        f"{record['message']}\n\n"
        f"Message ID: {record['id']}\n"
        f"Received: {record['created_at']} UTC"
    )
    sns.publish(TopicArn=TOPIC_ARN, Subject=subject, Message=message_body)


def _response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body_dict, ensure_ascii=False),
    }