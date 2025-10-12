from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, ChatSession, ChatMessage, TechStack
from app.schemas import (
    ChatMessageCreate, ChatMessageResponse, ChatResponse, 
    ChatSessionResponse, ChatHistoryRequest, ChatHistoryResponse
)
from app.auth import get_current_active_user
from app.services.openai_service import openai_service
import uuid

router = APIRouter()

@router.post("/session", response_model=ChatSessionResponse)
async def create_chat_session(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    session = ChatSession(
        session_id=str(uuid.uuid4()),
        user_id=current_user.id,
        title="New Chat"
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_user_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    limit: int = 20
):
    """Get user's chat sessions"""
    sessions = [session for session in current_user.chat_sessions if session.is_active]
    # Sort by most recent
    sessions.sort(key=lambda x: x.updated_at, reverse=True)
    return sessions[:limit]

@router.get("/session/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get messages from a specific chat session"""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return session.messages

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response"""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.session_id == message_data.session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        message_type="user",
        content=message_data.content
    )
    
    # Generate embeddings for the user message
    user_embedding = await openai_service.generate_embeddings(message_data.content)
    if user_embedding:
        user_message.embedding = user_embedding
    
    db.add(user_message)
    db.commit()
    
    # Get user's tech stack context
    tech_stack_data = []
    for tech in current_user.tech_stacks:
        tech_stack_data.append({
            'name': tech.name,
            'category': tech.category,
            'description': tech.description
        })
    
    # Get recent chat history for context
    recent_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.desc()).limit(10).all()
    
    chat_history = []
    for msg in reversed(recent_messages[:-1]):  # Exclude the message we just added
        chat_history.append({
            'message_type': msg.message_type,
            'content': msg.content
        })
    
    # Generate AI response
    try:
        ai_response_text = await openai_service.generate_chat_response(
            query=message_data.content,
            user_tech_stack=tech_stack_data,
            chat_history=chat_history
        )
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=session.id,
            message_type="assistant",
            content=ai_response_text,
            tech_context={"tech_stack": tech_stack_data}
        )
        
        # Generate embeddings for AI response
        ai_embedding = await openai_service.generate_embeddings(ai_response_text)
        if ai_embedding:
            ai_message.embedding = ai_embedding
        
        db.add(ai_message)
        
        # Update session timestamp
        session.updated_at = user_message.created_at
        
        # Update session title if it's the first exchange
        if len(session.messages) <= 2:  # user message + ai response
            # Generate a title based on the first message
            title_words = message_data.content.split()[:6]
            session.title = " ".join(title_words) + ("..." if len(title_words) == 6 else "")
        
        db.commit()
        
        return ChatResponse(
            message=ai_response_text,
            tech_context={"tech_stack": tech_stack_data},
            session_id=message_data.session_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response"
        )

@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    session.is_active = False
    db.commit()
    
    return {"message": "Chat session deleted successfully"}

@router.post("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    history_request: ChatHistoryRequest,
    db: Session = Depends(get_db)
):
    """Get chat history by username and optionally session_id"""
    # Find user by username
    user = db.query(User).filter(User.username == history_request.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build query for sessions
    sessions_query = db.query(ChatSession).filter(
        ChatSession.user_id == user.id,
        ChatSession.is_active == True
    )
    
    # If specific session_id is requested
    if history_request.session_id:
        sessions_query = sessions_query.filter(
            ChatSession.session_id == history_request.session_id
        )
    
    sessions = sessions_query.order_by(ChatSession.updated_at.desc()).limit(history_request.limit).all()
    
    # Get messages for each session
    messages_by_session = {}
    for session in sessions:
        session_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        messages_by_session[session.session_id] = session_messages
    
    return ChatHistoryResponse(
        sessions=sessions,
        messages=messages_by_session
    )