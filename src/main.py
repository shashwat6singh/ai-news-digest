"""
AI Policy News Digest — Main Runner
Fetches top 3 AI policy stories and sends them via email.

Environment variables required (set as GitHub Secrets):
  SENDER_EMAIL      — Gmail address you send FROM
  SENDER_PASSWORD   — Gmail App Password (NOT your account password)
  RECIPIENT_EMAIL   — Email address to deliver to (can be same as sender)
  MY_GIT_USERNAME   — Your GitHub username (for footer link)
"""

import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone

# Allow running from repo root or src/
sys.path.insert(0, os.path.dirname(__file__))

from fetch_news import get_top_stories
from email_template import build_email


def send_email(subject: str, html_body: str) -> None:
    sender = os.environ["SENDER_EMAIL"]
    password = os.environ["SENDER_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI Policy Digest <{sender}>"
    msg["To"] = recipient

    # Attach HTML (plain text fallback omitted for brevity — Gmail renders HTML fine)
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
        print(f"  Email sent to {recipient}")


def main():
    print(f"\n{'='*50}")
    print(f"  AI Policy Digest — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}\n")

    print("Fetching news from RSS sources...")
    stories = get_top_stories(n=3)

    if not stories:
        print("No stories found. Exiting without sending email.")
        sys.exit(0)

    print(f"\nTop {len(stories)} stories selected:")
    for i, s in enumerate(stories, 1):
        print(f"  {i}. [{s.score:.2f}] {s.source} — {s.title[:70]}...")

    github_user = os.environ.get("MY_GIT_USERNAME", "your-username")
    subject, html_body = build_email(stories, github_user=github_user)

    print("\nSending email...")
    send_email(subject, html_body)

    print("\nDone. ✓")


if __name__ == "__main__":
    main()
