from sqlalchemy import Column, Float, Integer, Text, Date, DateTime, Enum, ForeignKey, String
from enums import GroupRole
from datetime import datetime, timezone
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

def utcnow():
    return datetime.now(timezone.utc)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    ## dont forget to add relationships
    group = relationship("Group", back_populates="creator", foreign_keys="[Group.created_by]", cascade="all, delete-orphan")
    group_member = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    goalcompletion = relationship("GoalCompletion", back_populates="user", cascade="all, delete-orphan")
    quiz = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    streak = relationship("Streak", back_populates="user", cascade="all, delete-orphan")
    point_transaction = relationship("PointTransaction", back_populates="user", cascade="all, delete-orphan")
    resource = relationship("Resource", back_populates="user", cascade="all, delete-orphan")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    description = Column(String, nullable=True)
    invite_code = Column(String, unique=True, index=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    creator = relationship("User", back_populates="group", foreign_keys=[created_by])
    group_member = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    study_goal = relationship("StudyGoal", back_populates="group", cascade="all, delete-orphan")
    streak = relationship("Streak", back_populates="group", cascade="all, delete-orphan")
    resource = relationship("Resource", back_populates="group", cascade="all, delete-orphan")
    point_transaction = relationship("PointTransaction", back_populates="group", cascade="all, delete-orphan")


    
    
class GroupMember(Base):
    __tablename__ = "groupmembers"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user"),)  # so that one user cant enter the same group twice
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(GroupRole), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="group_member")
    group = relationship("Group", back_populates="group_member")
    


class StudyGoal(Base):
    __tablename__ = "studygoals"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    topic_content = Column(Text, nullable=False)
    week_number = Column(Integer, nullable=False)
    day_number = Column(Integer, nullable=True)
    deadline = Column(Date, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    group = relationship("Group", back_populates="study_goal")
    creator = relationship("User", foreign_keys=[created_by])
    goalcompletion = relationship("GoalCompletion", back_populates="study_goal", cascade="all, delete-orphan")
    quiz = relationship("Quiz", back_populates="study_goal", cascade="all, delete-orphan")


class GoalCompletion(Base):
    __tablename__ = "goalcompletions"
    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("studygoals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="goalcompletion")
    study_goal = relationship("StudyGoal", back_populates="goalcompletion")


class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("studygoals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    questions = Column(Text, nullable=False)
    answers = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    graded_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="quiz")
    study_goal = relationship("StudyGoal", back_populates="quiz")



class Streak(Base):
    __tablename__ = "streaks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_active_date = Column(Date, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="streak")
    group = relationship("Group", back_populates="streak")


class PointTransaction(Base):
    __tablename__ = "point_transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    created_at= Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="point_transaction")
    group = relationship("Group", back_populates="point_transaction")



class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False) # whether it is pdf, image or docs
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    group = relationship("Group", back_populates="resource")
    user = relationship("User", back_populates="resource")