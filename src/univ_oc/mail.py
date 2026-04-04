from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any, Optional


def send_update_email(
    *,
    to_addr: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    subject: str,
    body_text: str,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_addr
    msg.set_content(body_text)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port, timeout=60) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


def build_email_body(
    *,
    pages_base_url: str,
    changed_summaries: list[str],
    cumulative_brief: str,
) -> str:
    lines = [
        "【大学オープンキャンパス情報】更新がありました。",
        "",
        "■ 今回の更新（差分）",
        *changed_summaries,
        "",
        "■ 累積情報の要約",
        cumulative_brief,
        "",
        "■ 累積表・サイト",
        pages_base_url,
        "",
        "（このメールは更新があったときのみ送信されます）",
    ]
    return "\n".join(lines)


def load_smtp_settings_from_env() -> Optional[dict[str, Any]]:
    """Gmail 例: SMTP_HOST=smtp.gmail.com SMTP_PORT=587 SMTP_USER=... SMTP_PASSWORD=アプリパスワード"""
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    to_addr = os.environ.get("EMAIL_TO", user)
    if not user or not password:
        return None
    return {
        "smtp_host": host,
        "smtp_port": port,
        "smtp_user": user,
        "smtp_password": password,
        "email_to": to_addr,
    }
