"""
teams_notifier.py — Send messages to Microsoft Teams via webhook URL.
Set your webhook URL in the environment:
    $env:TEAMS_WEBHOOK_URL="https://nusu.webhook.office.com/webhookb2/055d87c4-5162-4f75-961f-8651f8d932ec@5ba5ef5e-3109-4e77-85bd-cfeb0d347e82/IncomingWebhook/1ed881a0154e415a9a062ff38cbddece/7e4d6980-86b2-415f-b293-6fcf0761d487/V2eb8Fq_8fcxJhthAwXPOHF2PP6l01UxDBcfBPOfKmKBE1"
"""
import os
import urllib.request
import json

WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL", "")

def send(message: str) -> bool:
    """
    Send a plain message to Teams.
    Returns True if successful, False if not.
    """
    if not WEBHOOK_URL:
        return False

    # Teams uses Adaptive Card format for rich messages
    payload = json.dumps({
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type":    "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True
                        }
                    ]
                }
            }
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception as e:
        print(f"  ⚠️  Teams 전송 실패: {e}")
        return False

def notify_question_and_answer(question: str, answer: str, sources: list = None):
    """Send a Q&A pair to Teams."""
    src_text = f"\n📄 출처: {', '.join(sources)}" if sources else ""
    message  = (
        f"🤝 **컨설턴트 에이전트 답변**\n\n"
        f"**Q:** {question}\n\n"
        f"**A:** {answer}"
        f"{src_text}"
    )
    return send(message)
