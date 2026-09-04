# services/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings


def send_email(to: str, subject: str, html_body: str):
    """Send HTML email using SMTP (Gmail)"""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject

        # Attach HTML (not plain text)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent to {to} — Subject: {subject}")  # ← Add this
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")  # ← Add this
        return False

    


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


def owner_created_email(to: str, username: str, group_name: str):
    """Sent when a user creates a group (auto-owner)"""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #4CAF50;">🎉 Group Created!</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p>You've successfully created the study group <strong>"{group_name}"</strong>.</p>
        <p>You're the <strong>Owner</strong> — you can invite members, create goals, and manage everything.</p>
        <p>Share the invite code with your classmates to get started!</p>
        <br>
        <p style="color: #666;">— The StudyGroup Team</p>
    </div>
    """
    send_email(to, f"🎉 You created '{group_name}'", html)


def member_joined_email(to: str, username: str, group_name: str):
    """Sent when a user joins a group"""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2196F3;">👋 Welcome to the Group!</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p>You've successfully joined <strong>"{group_name}"</strong>.</p>
        <p>You're now a <strong>Member</strong>. Check out the goals and start earning points!</p>
        <br>
        <p style="color: #666;">— The StudyGroup Team</p>
    </div>
    """
    send_email(to, f"👋 You joined '{group_name}'", html)


def admin_promoted_email(to: str, username: str, group_name: str):
    """Sent when a member is promoted to admin"""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #FF9800;">⭐ You've Been Promoted!</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p>You've been chosen as an <strong>Admin</strong> for <strong>"{group_name}"</strong>!</p>
        <p>You can now create, update, and manage study goals for the group.</p>
        <br>
        <p style="color: #666;">— The StudyGroup Team</p>
    </div>
    """
    send_email(to, f"⭐ You're now an Admin in '{group_name}'", html)


def member_demoted_email(to: str, username: str, group_name: str):
    """Sent when an admin is demoted to member"""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #f44336;">📋 Role Updated</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p>Your role in <strong>"{group_name}"</strong> has been changed to <strong>Member</strong>.</p>
        <p>You can still participate in quizzes, earn points, and join discussions.</p>
        <br>
        <p style="color: #666;">— The StudyGroup Team</p>
    </div>
    """
    send_email(to, f"📋 Role change in '{group_name}'", html)


def ownership_transferred_email(to: str, username: str, group_name: str):
    """Sent when ownership is transferred to a new owner"""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #9C27B0;">👑 You're the New Owner!</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p>Ownership of <strong>"{group_name}"</strong> has been transferred to you!</p>
        <p>You can now manage members, create goals, and control the group.</p>
        <br>
        <p style="color: #666;">— The StudyGroup Team</p>
    </div>
    """
    send_email(to, f"👑 You're now the Owner of '{group_name}'", html)


def member_left_group_email(to: str, username: str, group_name: str, left_username: str):
    """Sent to remaining admins when a member leaves"""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #607D8B;">👋 Member Left</h2>
        <p>Hey <strong>{username}</strong>,</p>
        <p><strong>{left_username}</strong> has left <strong>"{group_name}"</strong>.</p>
        <p>The group now has one less member. Keep the momentum going!</p>
        <br>
        <p style="color: #666;">— The StudyGroup Team</p>
    </div>
    """
    send_email(to, f"👋 {left_username} left '{group_name}'", html)



def group_invite_email(to: str, sender_username: str, group_name: str, invite_code: str):
    """Send invite code to a user's email"""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #4CAF50;">📚 You're Invited!</h2>
        <p>Hey!</p>
        <p><strong>{sender_username}</strong> invited you to join <strong>"{group_name}"</strong> on StudyGroup.</p>
        
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="margin: 0; color: #666;">Your invite code:</p>
            <h1 style="margin: 10px 0; color: #333; letter-spacing: 5px; font-size: 32px;">{invite_code}</h1>
        </div>
        
        <p>Use this code to join the group:</p>
        <p style="text-align: center;">
            <code style="background: #e8f5e9; padding: 8px 16px; border-radius: 4px;">
                POST /api/v1/groups/jointype="{invite_code}"
            </code>
        </p>
        
        <br>
        <p style="color: #666;">— The StudyGroup Team</p>
    </div>
    """
    send_email(to, f"📚 You're invited to '{group_name}'!", html)
