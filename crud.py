from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from models import (User, GroupMember, Group, 
                    StudyGoal, GoalCompletion, Quiz, Streak, PointTransaction, Resource)
from enums import GroupRole
from schemas import (GroupCreate,ResourceCreate, UserCreate,  GroupCreate, GroupUpdate, 
                    GoalCreate,GoalUpdate)
from core.security import verify_password, hashed_password
from datetime import date, timedelta
from models import utcnow
from utils import generate_invite_code
from services.gemini import generate_quiz_questions, grade_quiz_answers, strip_answers
import json
from datetime import date, datetime, timezone

from services.cloudinary import upload_file
from services.cache import get_cached, set_cache, invalidate_cache
from services.email import owner_created_email, member_joined_email, admin_promoted_email, member_demoted_email, ownership_transferred_email, member_left_group_email

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, username: str, password: str):
    db_user = get_user_by_username(db, username)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_user(db: Session, user: UserCreate):
    db_user = User(**user.model_dump(exclude={"password"}),
                   hashed_password=hashed_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_group(db: Session, group: GroupCreate, current_user: User):
    while True:
        invite_code = generate_invite_code()

        existing = db.query(Group).filter(Group.invite_code == invite_code).first()
        if not existing:
            break
    
    db_group = Group(**group.model_dump(),
                     created_by=current_user.id,
                     invite_code=invite_code)

    db.add(db_group)
    db.flush() # it get the id of the group before commit

    db_member = GroupMember(group_id=db_group.id,
                            user_id=current_user.id,
                            role=GroupRole.OWNER)
    db.add(db_member)

    db_streak = Streak( user_id=current_user.id, group_id=db_group.id)
    db.add(db_streak)

    
    db.commit()
    db.refresh(db_group)
    owner_created_email(to=current_user.email, username=current_user.username, group_name=db_group.name)
    return db_group

def get_my_groups(db:Session, current_user: User):
    groups = db.query(Group).join(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    
    return groups

def get_group_by_id(db:Session, group_id:int, current_user: User):
    group = db.query(Group).join(GroupMember).filter(Group.id == group_id, GroupMember.user_id == current_user.id).first()
    if not group:
        return None
    return group

def update_group(db:Session, group_id:int, group_update:GroupUpdate, current_user: User):
    group = db.query(Group).join(GroupMember).filter(Group.id == group_id, GroupMember.user_id == current_user.id, GroupMember.role.in_([GroupRole.ADMIN, GroupRole.OWNER])).first()
    if not group:
        return None

    update_data = group_update.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(group, key, value)
    
    db.commit()
    db.refresh(group)
    return group

def delete_group(db:Session, group_id:int, current_user: User):
    group = db.query(Group).join(GroupMember).filter(Group.id == group_id, GroupMember.user_id == current_user.id, GroupMember.role.in_([GroupRole.ADMIN, GroupRole.OWNER])).first()
    if not group:
        return None

    db.delete(group)
    db.commit()
    return group

def join_group(db: Session, invite_code: str, current_user: User):
    group = db.query(Group).filter(Group.invite_code == invite_code).first()
    if not group:
        return None

    existing_member = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.user_id == current_user.id
    ).first()
    if existing_member:
        return None

    db_member = GroupMember(group_id=group.id, user_id=current_user.id, role=GroupRole.MEMBER)
    db.add(db_member)
    db_streak = Streak(user_id=current_user.id, group_id=group.id)
    db.add(db_streak)
    db.commit()
    db.refresh(db_member)

    member_joined_email(to=current_user.email, username=current_user.username, group_name=group.name)
    invalidate_cache(f"dashboard:{current_user.id}:*")

    return {
        "id": db_member.id,
        "user_id": db_member.user_id,
        "username": current_user.username,
        "group_id": db_member.group_id,
        "role": db_member.role,
        "joined_at": db_member.joined_at
    }

def send_group_invite(db: Session, group_id: int, email: str, current_user: User):
    """Send invite code to a user's email"""
    from services.email import group_invite_email
    
    # Only owner/admin can invite
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role.in_([GroupRole.OWNER, GroupRole.ADMIN])
    ).first()
    if not member:
        return None, "Only owner/admin can invite"

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return None, "Group not found"

    # Send the invite email
    group_invite_email(
        to=email,
        sender_username=current_user.username,
        group_name=group.name,
        invite_code=group.invite_code
    )

    return {"message": f"Invite sent to {email}"}, None


def leave_group(db: Session, group_id: int, current_user: User):
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not member:
        return None

    if member.role == GroupRole.OWNER:
        return None

    if member.role == GroupRole.ADMIN:
        other_admins = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.role == GroupRole.ADMIN,
            GroupMember.user_id != current_user.id
        ).count()
        if other_admins == 0:
            return None

    member_data = {
        "id": member.id,
        "user_id": member.user_id,
        "username": current_user.username,
        "group_id": member.group_id,
        "role": member.role,
        "joined_at": member.joined_at
    }

    db.delete(member)
    db.commit()

    group = db.query(Group).filter(Group.id == group_id).first()
    remaining = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id != current_user.id
    ).all()

    for r in remaining:
        user = db.query(User).filter(User.id == r.user_id).first()
        if user and group:
            member_left_group_email(
                to=user.email, username=user.username,
                group_name=group.name, left_username=current_user.username
            )

    return member_data


def get_group_members(db: Session, group_id: int, current_user: User):
    group = db.query(Group).join(GroupMember).filter(
        Group.id == group_id, GroupMember.user_id == current_user.id
    ).first()
    if not group:
        return None

    members = (
        db.query(GroupMember, User.username)
        .join(User, User.id == GroupMember.user_id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "username": username,
            "group_id": m.group_id,
            "role": m.role,
            "joined_at": m.joined_at
        }
        for m, username in members
    ]


def promote_to_admin(db, group_id, user_id_to_promote, current_user):
    owner = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role == GroupRole.OWNER
    ).first()
    if not owner:
        return None

    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id_to_promote
    ).first()
    if not member:
        return None

    member.role = GroupRole.ADMIN
    db.commit()

    promoted_user = db.query(User).filter(User.id == user_id_to_promote).first()
    group = db.query(Group).filter(Group.id == group_id).first()
    if group and promoted_user:
        admin_promoted_email(to=promoted_user.email, username=promoted_user.username, group_name=group.name)

    return {
        "id": member.id,
        "user_id": member.user_id,
        "username": promoted_user.username if promoted_user else "Unknown",
        "group_id": member.group_id,
        "role": member.role,
        "joined_at": member.joined_at
    }


def demote_to_member(db, group_id, user_id_to_demote, current_user):
    owner = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role == GroupRole.OWNER
    ).first()
    if not owner:
        return None

    group = db.query(Group).filter(Group.id == group_id, Group.created_by == current_user.id).first()
    if not group:
        return None

    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id_to_demote
    ).first()
    if not member or member.user_id == current_user.id:
        return None

    member.role = GroupRole.MEMBER
    db.commit()

    demoted_user = db.query(User).filter(User.id == user_id_to_demote).first()
    if demoted_user:
        member_demoted_email(to=demoted_user.email, username=demoted_user.username, group_name=group.name)

    return {
        "id": member.id,
        "user_id": member.user_id,
        "username": demoted_user.username if demoted_user else "Unknown",
        "group_id": member.group_id,
        "role": member.role,
        "joined_at": member.joined_at
    }


def transfer_ownership(db, group_id, new_owner_id, current_user):
    current_owner = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role == GroupRole.OWNER
    ).first()
    if not current_owner:
        return None

    new_owner = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == new_owner_id,
        GroupMember.role == GroupRole.ADMIN
    ).first()
    if not new_owner:
        return None

    current_owner.role = GroupRole.ADMIN
    new_owner.role = GroupRole.OWNER
    db.commit()

    new_user = db.query(User).filter(User.id == new_owner_id).first()
    group = db.query(Group).filter(Group.id == group_id).first()
    if new_user and group:
        ownership_transferred_email(to=new_user.email, username=new_user.username, group_name=group.name)

    return {
        "id": new_owner.id,
        "user_id": new_owner.user_id,
        "username": new_user.username if new_user else "Unknown",
        "group_id": new_owner.group_id,
        "role": new_owner.role,
        "joined_at": new_owner.joined_at
    }


# Group Goals
def create_goal(db: Session, group_id: int, goal: GoalCreate, current_user: User):
    group_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role.in_([GroupRole.ADMIN, GroupRole.OWNER])
    ).first()
    if not group_member:
        return None

    

    db_goal = StudyGoal(**goal.model_dump(),
                        group_id=group_id,
                        created_by=current_user.id)
    if goal.deadline < date.today():
        return None  # Deadline cannot be in the past
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    invalidate_cache(f"goals:{group_id}:*")
    return db_goal

def get_group_goals(db: Session, group_id: int, current_user: User, week_number: int = None, ):
    group_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not group_member:
        return None

    query = db.query(StudyGoal).filter(StudyGoal.group_id == group_id)

    if week_number is not None:
        query = query.filter(StudyGoal.week_number == week_number)
    goals = query.all()
    
    return goals

def get_goal_by_id(db: Session, goal_id: int, current_user: User):
    goal = db.query(StudyGoal).join(GroupMember, StudyGoal.group_id == GroupMember.group_id).filter(
        StudyGoal.id == goal_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not goal:
        return None
    return goal

def update_goal(db: Session, goal_id: int, goal_update: GoalUpdate, current_user: User):
    goal = db.query(StudyGoal).join(GroupMember, StudyGoal.group_id == GroupMember.group_id).filter(
        StudyGoal.id == goal_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role.in_([GroupRole.ADMIN, GroupRole.OWNER])
    ).first()
    if not goal:
        return None

    update_data = goal_update.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(goal, key, value)

    db.commit()
    db.refresh(goal)
    return goal

def delete_goal(db: Session, goal_id: int, current_user: User):
    goal = db.query(StudyGoal).join(GroupMember, StudyGoal.group_id == GroupMember.group_id).filter(
        StudyGoal.id == goal_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role.in_([GroupRole.ADMIN, GroupRole.OWNER])
    ).first()
    if not goal:
        return None

    db.delete(goal)
    db.commit()
    invalidate_cache(f"goals:{goal.group_id}:*")
    return goal



# gemini quiz functions

async def start_quiz(db: Session, goal_id: int, current_user: User):
    goal = db.query(StudyGoal).join(GroupMember, StudyGoal.group_id == GroupMember.group_id).filter(
        StudyGoal.id == goal_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not goal:
        return None

    existing_quiz = db.query(Quiz).filter(
        Quiz.goal_id == goal_id,
        Quiz.user_id == current_user.id,
        Quiz.created_at >= date.today()
    ).first()
    if existing_quiz:
        raise HTTPException(status_code=400, detail="Quiz already taken")  # User has already started the quiz

    questions = await generate_quiz_questions(goal.topic_content)

    new_quiz = Quiz(goal_id=goal_id, user_id=current_user.id, questions=json.dumps(questions))



    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    invalidate_cache(f"leaderboard:{goal.group_id}:*")
    invalidate_cache(f"dashboard:{current_user.id}:*")
    return {
        "id": new_quiz.id,
        "goal_id": new_quiz.goal_id,
        "user_id": new_quiz.user_id,
        "questions": json.loads(new_quiz.questions) if new_quiz.questions else None,
        "answers": json.loads(new_quiz.answers) if new_quiz.answers else None,
        "score": new_quiz.score,
        "feedback": json.loads(new_quiz.feedback) if new_quiz.feedback else None,
        "created_at": new_quiz.created_at,
        "graded_at": new_quiz.graded_at,
    }





async def submit_quiz(db: Session, quiz_id: int, answers: list[str], current_user: User):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if quiz.graded_at is not None:
        raise HTTPException(status_code=400, detail="Quiz already graded")

    goal = db.query(StudyGoal).filter(StudyGoal.id == quiz.goal_id).first()
    questions = json.loads(quiz.questions)

    result = await grade_quiz_answers(goal.topic_content, questions, answers)

    # ── Save grading (ONE block, JSON strings — matches the schema) ──
    quiz.answers = json.dumps(answers)
    quiz.feedback = json.dumps(result.get("results", []))
    quiz.score = result.get("total_score", 0)
    quiz.graded_at = datetime.now(timezone.utc)

    # ── Award points ──
    max_score = result.get("max_score", 10) or 10
    percentage = result.get("total_score", 0) / max_score
    points = max(3, int(percentage * 20))

    db.add(PointTransaction(
        user_id=current_user.id,
        group_id=goal.group_id,
        amount=points,
        reason=f"Quiz score: {result.get('total_score', 0)}/{max_score}"
    ))

    # ── Update streak ──
    streak = db.query(Streak).filter(
        Streak.user_id == current_user.id,
        Streak.group_id == goal.group_id
    ).first()
    if streak:
        streak.current_streak += 1
        streak.last_active_date = date.today()
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

    # ── Goal completion ──
    if percentage >= 0.5:
        db.add(GoalCompletion(user_id=current_user.id, goal_id=goal.id))

    db.commit()
    db.refresh(quiz)

    return {
        "id": quiz.id,
        "goal_id": quiz.goal_id,
        "user_id": quiz.user_id,
        "questions": json.loads(quiz.questions) if quiz.questions else None,
        "answers": json.loads(quiz.answers) if quiz.answers else None,
        "score": quiz.score,
        "feedback": json.loads(quiz.feedback) if quiz.feedback else None,
        "created_at": quiz.created_at,
        "graded_at": quiz.graded_at,
    }
  # ← ORM object: answers/feedback/questions serialize as JSON strings

def add_points(db: Session, user_id: int, group_id: int, amount: int, reason: str):
    points = PointTransaction(user_id=user_id, group_id=group_id, amount=amount, reason=reason)
    db.add(points)
    db.commit()
    db.refresh(points)
    invalidate_cache(f"leaderboard:{group_id}:*")
    invalidate_cache(f"dashboard:{user_id}:*")
    return points

def get_total_points(db: Session, user_id: int, group_id: int):
    total = db.query(PointTransaction).filter(
        PointTransaction.user_id == user_id,
        PointTransaction.group_id == group_id
    ).with_entities(func.sum(PointTransaction.amount)).scalar()
    return total or 0


def get_or_create_streak(db: Session, user_id: int, group_id: int):
    streak = db.query(Streak).filter(
        Streak.user_id == user_id,
        Streak.group_id == group_id
    ).first()
    if not streak:
        streak = Streak(user_id=user_id, group_id=group_id)
        db.add(streak)
        db.commit()
        db.refresh(streak)
    return streak

def update_streak(db: Session, user_id: int, group_id: int, passed: bool):
    streak = get_or_create_streak(db, user_id, group_id)
    today = date.today()

    if streak.last_active_date == today:
        return streak

    if passed:
        if streak.last_active_date == today - timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1

    else:
        streak.current_streak = 0


    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak

    streak.last_active_date = today
    
    db.commit()
    db.refresh(streak)
    return streak


def get_group_leaderboard(db: Session, group_id: int, week_number: int = None):
    cache_key = f"leaderboard:{group_id}:{week_number}"


    # check cache first
    cached = get_cached(cache_key)
    if cached:
        return cached
    

    members = ( db.query(GroupMember, User.username).join(User, User.id == GroupMember.user_id).filter(GroupMember.group_id == group_id).all() )
    leaderboard = []

    for member, username in members:
        user_id = member.user_id

        points_filter = [PointTransaction.user_id == user_id, 
                         PointTransaction.group_id == group_id]

        if week_number is not None:
           points_filter.append(PointTransaction.created_at >= get_week_start(week_number))
           points_filter.append(PointTransaction.created_at < get_week_start(week_number + 1))

        total_points = db.query(func.coalesce(func.sum(PointTransaction.amount), 0)).filter(*points_filter).scalar()

        quiz_filter = [Quiz.user_id == user_id, StudyGoal.group_id == group_id, Quiz.graded_at.isnot(None)]

        if week_number is not None:
            quiz_filter.append(StudyGoal.week_number == week_number)

        quizzes_completed = db.query(func.count(Quiz.id)).join(StudyGoal, StudyGoal.id == Quiz.goal_id).filter(*quiz_filter).scalar()

        streak = db.query(Streak).filter(Streak.user_id == user_id, Streak.group_id == group_id).first()

        current_streak = streak.current_streak if streak else 0

        avg_filter = [Quiz.user_id == user_id, 
                      StudyGoal.group_id == group_id,
                      Quiz.score.isnot(None)]

        if week_number is not None:
            avg_filter.append(StudyGoal.week_number == week_number)
        
        avg_score = db.query(
            func.coalesce(func.avg(Quiz.score), 0.0)
        ).join(
            StudyGoal, Quiz.goal_id == StudyGoal.id
        ).filter(*avg_filter).scalar()
        
        leaderboard.append({
            "user_id": user_id,
            "username": username,
            "total_points": total_points,
            "current_streak": current_streak,
            "quizzes_completed": quizzes_completed,
            "avg_score": round(float(avg_score), 2)
        })

    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
   
    for i, entry in enumerate(leaderboard, 1):
        entry["rank"] = i

    set_cache(cache_key, leaderboard, ttl_seconds=300)
    return leaderboard

def get_week_start(week_number: int):
    """Get the Monday start date for a given ISO week number"""
    
    jan1 = date(date.today().year, 1, 1)
    # Find the Monday of the given week
    start = jan1 + timedelta(weeks=week_number - 1, days=-jan1.weekday())
    return start





# Resources
def upload_resource(db: Session, group_id:int, resource: ResourceCreate, current_user: User):
    
    member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first()
    if not member:
            return None

    db_resource = Resource(
        group_id=group_id,
        uploaded_by=current_user.id,
        title=resource.title,
        description=resource.description,
        file_url=resource.file_url,
        file_type=resource.file_type.value
    )
    
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource

def get_group_resources(db: Session, group_id: int, current_user: User):
    # Check membership
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not member:
        return None

    resources = db.query(Resource).filter(Resource.group_id == group_id).all()
    return resources


def get_resource_by_id(db: Session, resource_id: int, current_user: User):
    resource = db.query(Resource).join(
        GroupMember, Resource.group_id == GroupMember.group_id
    ).filter(
        Resource.id == resource_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    return resource  


def delete_resource(db: Session, resource_id: int, current_user: User):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        return None

    # Check if user is uploader
    if resource.uploaded_by == current_user.id:
        db.delete(resource)
        db.commit()
        return resource

    
    member = db.query(GroupMember).filter(
        GroupMember.group_id == resource.group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role.in_([GroupRole.OWNER, GroupRole.ADMIN])
    ).first()
    if not member:
        return None

# dashboard

def get_dashboard(db: Session, current_user: User):
    today = date.today()
    next_week = today + timedelta(days=7)

    groups = (
        db.query(Group).join(GroupMember, GroupMember.group_id == Group.id).filter(GroupMember.user_id == current_user.id).all() )

    group_ids = [g.id for g in groups]

    pending_goals = (
        db.query(StudyGoal).filter(StudyGoal.group_id.in_(group_ids), StudyGoal.deadline >= today)
        .except_(
            db.query(StudyGoal)
            .join(GoalCompletion, GoalCompletion.goal_id == StudyGoal.id)
            .filter(GoalCompletion.user_id == current_user.id)
        )
        .all()
    )
    upcoming_deadlines = (db.query(StudyGoal).filter(StudyGoal.group_id.in_(group_ids),StudyGoal.deadline >= today,
            StudyGoal.deadline <= next_week
        )
        .order_by(StudyGoal.deadline)
        .all()
    )

    total_points = db.query(
        func.coalesce(func.sum(PointTransaction.amount), 0)
    ).filter(
        PointTransaction.user_id == current_user.id,
        PointTransaction.group_id.in_(group_ids)
    ).scalar()

    streaks = db.query(Streak).filter(
        Streak.user_id == current_user.id,
        Streak.group_id.in_(group_ids)
    ).all()

    current_streak = sum(s.current_streak for s in streaks)
    longest_streak = max((s.longest_streak for s in streaks), default=0)

    return {
        "groups": groups,
        "pending_goals": pending_goals,
        "upcoming_deadlines": upcoming_deadlines,
        "total_points": total_points,
        "current_streak": current_streak,
        "longest_streak": longest_streak
    }


def get_user_stats(db: Session, user_id: int, group_id: int, current_user:User):

    if current_user:
        member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first()
        if not member:
            return None

            
    total_points = db.query(
        func.coalesce(func.sum(PointTransaction.amount), 0)
    ).filter(
        PointTransaction.user_id == user_id,
        PointTransaction.group_id == group_id
    ).scalar()

    
    streak = db.query(Streak).filter(
        Streak.user_id == user_id,
        Streak.group_id == group_id
    ).first()

    current_streak = streak.current_streak if streak else 0
    longest_streak = streak.longest_streak if streak else 0

    
    quizzes_taken = db.query(
        func.count(Quiz.id)
    ).join(
        StudyGoal, Quiz.goal_id == StudyGoal.id
    ).filter(
        Quiz.user_id == user_id,
        StudyGoal.group_id == group_id,
        Quiz.graded_at.isnot(None)  # Only graded quizzes
    ).scalar()

   
    avg_score = db.query(
        func.coalesce(func.avg(Quiz.score), 0.0)
    ).join(
        StudyGoal, Quiz.goal_id == StudyGoal.id
    ).filter(
        Quiz.user_id == user_id,
        StudyGoal.group_id == group_id,
        Quiz.score.isnot(None)
    ).scalar()

    
    goals_completed = db.query(
        func.count(GoalCompletion.id)
    ).join(
        StudyGoal, GoalCompletion.goal_id == StudyGoal.id
    ).filter(
        GoalCompletion.user_id == user_id,
        StudyGoal.group_id == group_id
    ).scalar()

    
    members_with_more_points = db.query(
        func.count(PointTransaction.user_id)
    ).filter(
        PointTransaction.group_id == group_id,
        PointTransaction.amount > 0
    ).group_by(
        PointTransaction.user_id
    ).having(
        func.sum(PointTransaction.amount) > total_points
    ).count()

    rank = members_with_more_points + 1

    return {
        "user_id": user_id,
        "group_id": group_id,
        "total_points": total_points,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "quizzes_taken": quizzes_taken,
        "avg_score": round(float(avg_score), 2),
        "goals_completed": goals_completed,
        "rank": rank
    }