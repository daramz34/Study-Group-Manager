# services/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, timedelta
from database import SessionLocal
from models import StudyGoal, GroupMember, User, Streak, GoalCompletion
from services.email import (
    deadline_reminder,
    weekly_digest,
    streak_alert
)

scheduler = BackgroundScheduler()


# ── DEADLINE REMINDER — Daily at 8 AM ──
@scheduler.scheduled_job(CronTrigger(hour=8, minute=0))
def send_deadline_reminders():
    db = SessionLocal()
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)

        upcoming_goals = db.query(StudyGoal).filter(
            StudyGoal.deadline.in_([today, tomorrow])
        ).all()

        for goal in upcoming_goals:
            members = db.query(GroupMember).filter(
                GroupMember.group_id == goal.group_id
            ).all()

            for member in members:
                completed = db.query(GoalCompletion).filter(
                    GoalCompletion.goal_id == goal.id,
                    GoalCompletion.user_id == member.user_id
                ).first()
                if completed:
                    continue

                user = db.query(User).filter(User.id == member.user_id).first()
                if not user:
                    continue

                days_left = (goal.deadline - today).days

                deadline_reminder(
                    to=user.email,
                    username=user.username,
                    goal_title=goal.title,
                    days_left=days_left
                )
    finally:
        db.close()


# ── WEEKLY DIGEST — Sunday at 8 PM ──
@scheduler.scheduled_job(CronTrigger(day_of_week="sun", hour=20, minute=0))
def send_weekly_digests():
    db = SessionLocal()
    try:
        groups = db.query(GroupMember.group_id).distinct().all()

        for (group_id,) in groups:
            # Get actual group name
            from models import Group
            group = db.query(Group).filter(Group.id == group_id).first()
            group_name = group.name if group else f"Group {group_id}"

            members = db.query(GroupMember).filter(
                GroupMember.group_id == group_id
            ).all()

            member_stats = []
            for m in members:
                user = db.query(User).filter(User.id == m.user_id).first()
                streak = db.query(Streak).filter(
                    Streak.user_id == m.user_id,
                    Streak.group_id == group_id
                ).first()

                member_stats.append({
                    "username": user.username if user else "Unknown",
                    "streak": streak.current_streak if streak else 0
                })

            # Call Gemini for AI summary
            from services.gemini import generate_weekly_digest
            digest = generate_weekly_digest(
                group_name=group_name,
                member_stats=member_stats
            )

            # Send to all members
            for m in members:
                user = db.query(User).filter(User.id == m.user_id).first()
                if user:
                    weekly_digest(
                        to=user.email,
                        username=user.username,
                        group_name=group_name,
                        digest_text=digest
                    )
    finally:
        db.close()


# ── STREAK CHECK — Daily at midnight ──
@scheduler.scheduled_job(CronTrigger(hour=0, minute=0))
def check_streaks():
    db = SessionLocal()
    try:
        yesterday = date.today() - timedelta(days=1)

        stale_streaks = db.query(Streak).filter(
            Streak.last_active_date != yesterday,
            Streak.last_active_date.isnot(None),
            Streak.current_streak > 0
        ).all()

        for streak in stale_streaks:
            old_count = streak.current_streak
            streak.current_streak = 0
            db.commit()

            # Send streak reset email
            user = db.query(User).filter(User.id == streak.user_id).first()
            if user:
                streak_alert(
                    to=user.email,
                    username=user.username,
                    current_streak=old_count
                )
    finally:
        db.close()


def start_scheduler():
    scheduler.start()
    print("✅ Scheduler started")


def shutdown_scheduler():
    scheduler.shutdown(wait=False)
    print("🛑 Scheduler stopped")
