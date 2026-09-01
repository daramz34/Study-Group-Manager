from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import (User, GroupMember, Group, 
                    StudyGoal, GoalCompletion, Quiz, Streak, PointTransaction, Resource)
from enums import GroupRole
from schemas import (GroupCreate, UserCreate,  GroupCreate, GroupUpdate, 
                    GoalCreate,GoalUpdate)
from core.security import verify_password, hashed_password
from datetime import date, timedelta
from models import utcnow
from utils import generate_invite_code
from services.gemini import generate_quiz_questions, grade_quiz_answers
import json

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
    return db_group

def get_my_groups(db:Session, current_user: User):
    groups = db.query(Group).join(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    if not groups:
        return None
    return groups

def get_group_by_id(db:Session, group_id:int, current_user: User):
    group = db.query(Group).join(GroupMember).filter(Group.id == group_id, GroupMember.user_id == current_user.id).first()
    if not group:
        return None
    return group

def update_group(db:Session, group_id:int, group_update:GroupUpdate, current_user: User):
    group = db.query(Group).join(GroupMember).filter(Group.id == group_id, GroupMember.user_id == current_user.id, GroupMember.role == GroupRole.ADMIN).first()
    if not group:
        return None

    update_data = group_update.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(group, key, value)
    
    db.commit()
    db.refresh(group)
    return group

def delete_group(db:Session, group_id:int, current_user: User):
    group = db.query(Group).join(GroupMember).filter(Group.id == group_id, GroupMember.user_id == current_user.id, GroupMember.role == GroupRole.ADMIN).first()
    if not group:
        return None

    db.delete(group)
    db.commit()
    return group

def join_group(db:Session, invite_code:str, current_user: User):
    group = db.query(Group).filter(Group.invite_code == invite_code).first()
    if not group:
        return None

    existing_member = db.query(GroupMember).filter(GroupMember.group_id == group.id, GroupMember.user_id == current_user.id).first()
    if existing_member:
        return None

    db_member = GroupMember(group_id=group.id,
                            user_id=current_user.id,
                            role=GroupRole.MEMBER)
    db.add(db_member)

    db_streak = Streak(user_id=current_user.id, group_id=group.id)
    db.add(db_streak)

    db.commit()
    db.refresh(db_member)
    return db_member


def leave_group(db:Session, group_id:int, current_user: User):
    member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not member:
        return None

    if member.role == GroupRole.OWNER:
        return None  # Owner cannot leave the group without transferring ownership
    
    if member.role == GroupRole.ADMIN:
        other_admins = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.role == GroupRole.ADMIN,
            GroupMember.user_id != current_user.id
        ).count()
        
        if other_admins == 0:
            return None
    db.delete(member)
    db.commit()
    return member

def get_group_members(db:Session, group_id:int, current_user: User):
    group = db.query(Group).join(GroupMember).filter(Group.id == group_id, GroupMember.user_id == current_user.id).first()
    if not group:
        return None

    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    return members



def promote_to_admin(db, group_id, user_id_to_promote, current_user):
    
    owner = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role == GroupRole.OWNER).first()
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
    db.refresh(member)
    return member


def demote_to_member(db, group_id, user_id_to_demote, current_user):
    # Only owner can demote
    owner = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role == GroupRole.OWNER).first()
    if not owner:
        return None

    group = db.query(Group).filter(
        Group.id == group_id,
        Group.created_by == current_user.id
    ).first()
    if not group:
        return None

    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id_to_demote
    ).first()
    if not member or member.user_id == current_user.id:
        return None  # Can't demote yourself

    member.role = GroupRole.MEMBER
    db.commit()
    return member

def transfer_ownership(db, group_id, new_owner_id, current_user):
    # Only current owner can transfer ownership
    current_owner = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.role == GroupRole.OWNER).first()
    if not current_owner:
        return None

    new_owner = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == new_owner_id,
        GroupMember.role == GroupRole.ADMIN
    ).first()
    if not new_owner:
        return None

    # we have to demote the current owner to admin and promote the new owner to owner
    current_owner.role = GroupRole.ADMIN  

    # promote the new_owner to owner
    new_owner.role = GroupRole.OWNER  

    db.commit()
    return new_owner


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
    if db_goal.deadline < date.today():
        return None  # Deadline cannot be in the past
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
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
        return None  # User has already started the quiz

    questions = await generate_quiz_questions(goal.topic_content)

    new_quiz = Quiz(goal_id=goal_id, user_id=current_user.id, questions=json.dumps(questions))



    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    return new_quiz


async def submit_quiz(db: Session, quiz_id: int, answers: list[str], current_user: User):
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == current_user.id
    ).first()
    if not quiz:
        return None,"Quiz not found"
    if quiz.graded_at is not None:
        return None, "Already graded" # Quiz has already been graded

    

    goal = db.query(StudyGoal).filter(StudyGoal.id == quiz.goal_id).first()
    questions = json.loads(quiz.questions)

    result = await grade_quiz_answers(goal.topic_content, questions, answers)

    max_score = result.get("max_score", 0)
    percentage = result["total_score"] / max_score if max_score > 0 else 0
    points_earned = max(3, int(percentage * 20))  



    

    quiz.answers = json.dumps(answers)
    quiz.score = result["total_score"]
    quiz.feedback = json.dumps(result["results"])
    quiz.graded_at = utcnow()

    points = PointTransaction(user_id=current_user.id, group_id=goal.group_id, amount=points_earned, reason=f"Quiz score: {result['total_score']}/{max_score}")

    db.add(points)

    passed = percentage >= 0.5
    update_streak(db,current_user.id, goal.group_id, passed)

    if passed:
        completion = GoalCompletion(goal_id=goal.id, user_id=current_user.id)
        db.add(completion)
    db.commit()
    db.refresh(quiz)
    return quiz