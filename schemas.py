from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime, date
from enums import GroupRole, FileType



class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserStatsResponse(BaseModel):
    user_id: int
    group_id: int
    total_points: int
    current_streak: int
    longest_streak: int
    quizzes_taken: int
    avg_score: float
    goals_completed: int
    rank: int

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"




class GroupCreate(BaseModel):
    name: str
    subject: str
    description: Optional[str] = None

class GroupResponse(BaseModel):
    id: int
    name: str
    subject: str
    description: Optional[str] = None
    invite_code: str
    created_by: int
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None


#  for Group members

class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    group_id: int
    role: GroupRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JoinGroupRequest(BaseModel):
    invite_code: str

class PostionRequest(BaseModel):
    user_id: int

# for study goals

class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    topic_content: str
    week_number: int
    day_number: Optional[int] = None
    deadline: date

class GoalResponse(BaseModel):
    id: int
    group_id: int
    title: str
    description: Optional[str] = None
    topic_content: str
    week_number: int
    day_number: Optional[int] = None
    deadline: date
    created_by: int
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    topic_content: Optional[str] = None
    week_number: Optional[int] = None
    day_number: Optional[int] = None
    deadline: Optional[date] = None


# for goal completion

class GoalCompletionResponse(BaseModel):
    id: int
    goal_id: int
    user_id: int
    completed_at:datetime

    model_config = ConfigDict(from_attributes=True)



# for quiz

class QuizResponse(BaseModel):
    id: int
    goal_id: int
    user_id: int
    questions: str
    answers: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    created_at: datetime
    graded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SubmitAnswers(BaseModel):
    answers: list[str]



# streaks
class StreakResponse(BaseModel):
    id: int
    user_id: int
    group_id: int
    current_streak: int
    longest_streak: int
    last_active_date: Optional[date] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


#points
class PointTransactionResponse(BaseModel):
    id: int
    user_id: int
    group_id: int
    amount: int
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# leaderboard

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    total_points: int
    current_streak: int
    quizzes_completed: int


class LeaderboardResponse(BaseModel):
    group_id: int
    week_number: int
    entries: list[LeaderboardEntry]

    model_config = ConfigDict(from_attributes=True)

# resources
class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    file_url : str
    file_type: FileType

class ResourceResponse(BaseModel):
    id: int
    group_id: int
    uploaded_by: int
    title: str
    description: Optional[str] = None
    file_url: str
    file_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# dashboard

class DashboardResponse(BaseModel):
    groups: list[GroupResponse]
    pending_goals: list[GoalResponse]
    upcoming_deadlines: list[GoalResponse]
    total_points: int
    current_streak: int
    longest_streak: int
    
    model_config = ConfigDict(from_attributes=True)

