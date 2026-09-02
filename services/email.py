# services/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings


def send_email(to: str, subject: str, html_body: str):
    """Send HTML email using SMTP (Gmail)"""
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject

    # Attach HTML (not plain text)
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)


# ── EMAIL TEMPLATES ──

BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; }}
        .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
        .header p {{ color: #e0e0e0; margin: 5px 0 0; font-size: 14px; }}
        .content {{ padding: 30px; color: #333333; line-height: 1.6; }}
        .content h2 {{ color: #667eea; margin-top: 0; }}
        .btn {{ display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 15px 0; }}
        .stat-box {{ background: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }}
        .stat-label {{ font-size: 12px; color: #888; text-transform: uppercase; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #888; }}
        .urgent {{ color: #e74c3c; font-weight: bold; }}
        .success {{ color: #27ae60; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 StudyGroup</h1>
            <p>Learn Together, Rank Together</p>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>StudyGroup — Keep learning, keep ranking 🏆</p>
        </div>
    </div>
</body>
</html>
"""


def deadline_reminder(to: str, username: str, goal_title: str, days_left: int):
    """Send deadline reminder email"""
    urgency = "today!" if days_left == 0 else f"in {days_left} day(s)"
    color_class = "urgent" if days_left <= 1 else ""

    content = f"""
        <h2>⏰ Deadline Reminder</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p>Your study goal is due <span class="{color_class}">{urgency}</span></p>
        <div class="stat-box">
            <div class="stat-label">Goal</div>
            <div class="stat-value">{goal_title}</div>
        </div>
        <p>Don't forget to take the quiz to keep your streak alive! 🔥</p>
        <a href="#" class="btn">Take Quiz Now</a>
    """

    html = BASE_TEMPLATE.format(content=content)
    send_email(to, f"⏰ Goal Due {urgency} — {goal_title}", html)


def weekly_digest(to: str, username: str, group_name: str, digest_text: str):
    """Send weekly digest email with Gemini summary"""
    content = f"""
        <h2>📊 Weekly Digest</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p>Here's what happened in <strong>{group_name}</strong> this week:</p>
        <div class="stat-box">
            <p>{digest_text}</p>
        </div>
        <p>Keep pushing! Check the leaderboard to see where you stand. 🏆</p>
        <a href="#" class="btn">View Leaderboard</a>
    """

    html = BASE_TEMPLATE.format(content=content)
    send_email(to, f"📊 Weekly Digest — {group_name}", html)


def welcome_email(to: str, username: str):
    """Send welcome email after registration"""
    content = f"""
        <h2>👋 Welcome to StudyGroup!</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p>You're all set! Here's what you can do:</p>
        <div class="stat-box">
            <p>✅ Create or join study groups</p>
            <p>✅ Take AI-generated quizzes</p>
            <p>✅ Climb the leaderboard</p>
            <p>✅ Track your streak 🔥</p>
        </div>
        <p>Start by joining a group or creating one with your classmates!</p>
        <a href="#" class="btn">Get Started</a>
    """

    html = BASE_TEMPLATE.format(content=content)
    send_email(to, "👋 Welcome to StudyGroup!", html)


def streak_alert(to: str, username: str, current_streak: int):
    """Send streak warning — user missed a day"""
    content = f"""
        <h2>🔥 Streak Alert!</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p>Your streak was <span class="urgent">reset</span> because you missed yesterday's quiz.</p>
        <div class="stat-box">
            <div class="stat-label">Previous Streak</div>
            <div class="stat-value">{current_streak} days 🔥</div>
        </div>
        <p>Don't let it happen again! Take today's quiz to start a new streak.</p>
        <a href="#" class="btn">Start New Streak</a>
    """

    html = BASE_TEMPLATE.format(content=content)
    send_email(to, "🔥 Your Streak Was Reset!", html)
