"""
slack_notifier.py — Send messages to Slack via webhook URL.
Set your webhook URL in the environment:
    $env:SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx/yyy/zzz"
"""
import os
import urllib.request
import json

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

def send(message: str) -> bool:
    """
    Send a message to Slack.
    Returns True if successful, False if not.
    """
    if not WEBHOOK_URL:
        return False

    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception as e:
        print(f"  ⚠️  Slack 전송 실패: {e}")
        return False

def notify_question_and_answer(question: str, answer: str, sources: list = None):
    """Send a Q&A pair to Slack."""
    src_text = f"\n📄 출처: {', '.join(sources)}" if sources else ""
    message  = (
        f"*🤝 컨설턴트 에이전트 답변*\n"
        f"*Q:* {question}\n"
        f"*A:* {answer}"
        f"{src_text}"
    )
    return send(message)
