from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    years_of_experience: Optional[int] = Field(default=0, ge=0)
    current_role: Optional[str] = None

class UserResponse(UserBase):
    id: int
    years_of_experience: int
    current_role: Optional[str]
    is_active: bool
    created_at: datetime
    tech_stacks: List["TechStackResponse"] = []
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    years_of_experience: Optional[int] = None
    current_role: Optional[str] = None

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# Tech Stack schemas
class TechStackBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None

class TechStackCreate(TechStackBase):
    pass

class TechStackResponse(TechStackBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TechStackUpdate(BaseModel):
    tech_stack_ids: List[int]

# Chat schemas
class ChatSessionBase(BaseModel):
    title: Optional[str] = "New Chat"

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionResponse(ChatSessionBase):
    id: int
    session_id: str
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    content: str
    message_type: str = Field(..., pattern="^(user|assistant)$")

class ChatMessageCreate(BaseModel):
    content: str
    session_id: str

class ChatMessageResponse(ChatMessageBase):
    id: int
    session_id: int
    tech_context: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    message: str
    tech_context: Optional[Dict[str, Any]] = None
    session_id: str

# Interview schemas
class InterviewQuestionBase(BaseModel):
    question: str
    category: str
    difficulty_level: str
    tech_stack: Optional[str] = None
    expected_answer: Optional[str] = None

class InterviewQuestionResponse(InterviewQuestionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class InterviewQuestionRequest(BaseModel):
    years_of_experience: int = Field(..., ge=0, le=50)
    target_role: str
    focus_areas: Optional[List[str]] = []
    num_questions: Optional[int] = Field(default=5, ge=1, le=20)

class InterviewQuestionSet(BaseModel):
    questions: List[InterviewQuestionResponse]
    user_context: Dict[str, Any]

# Chat history schemas
class ChatHistoryRequest(BaseModel):
    session_id: Optional[str] = None
    username: str
    limit: Optional[int] = Field(default=50, le=100)

class ChatHistoryResponse(BaseModel):
    sessions: List[ChatSessionResponse]
    messages: Dict[str, List[ChatMessageResponse]]

# Update forward references
UserResponse.model_rebuild()