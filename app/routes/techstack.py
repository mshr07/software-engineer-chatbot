from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, TechStack
from app.schemas import TechStackResponse, TechStackCreate, TechStackUpdate
from app.auth import get_current_active_user

router = APIRouter()

@router.get("/available", response_model=List[TechStackResponse])
async def get_available_tech_stacks(
    category: str = None,
    db: Session = Depends(get_db)
):
    """Get all available tech stacks, optionally filtered by category"""
    query = db.query(TechStack)
    if category:
        query = query.filter(TechStack.category == category)
    
    tech_stacks = query.all()
    return tech_stacks

@router.get("/categories")
async def get_tech_stack_categories(db: Session = Depends(get_db)):
    """Get all available tech stack categories"""
    categories = db.query(TechStack.category).distinct().all()
    return {"categories": [cat[0] for cat in categories]}

@router.post("/create", response_model=TechStackResponse)
async def create_tech_stack(
    tech_stack: TechStackCreate,
    db: Session = Depends(get_db)
):
    """Create a new tech stack (admin function)"""
    # Check if tech stack already exists
    existing = db.query(TechStack).filter(TechStack.name == tech_stack.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tech stack already exists"
        )
    
    db_tech_stack = TechStack(**tech_stack.dict())
    db.add(db_tech_stack)
    db.commit()
    db.refresh(db_tech_stack)
    
    return db_tech_stack

@router.get("/my-stack", response_model=List[TechStackResponse])
async def get_user_tech_stack(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's tech stack"""
    return current_user.tech_stacks

@router.put("/my-stack")
async def update_user_tech_stack(
    tech_stack_update: TechStackUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's tech stack"""
    # Get tech stacks by IDs
    tech_stacks = db.query(TechStack).filter(
        TechStack.id.in_(tech_stack_update.tech_stack_ids)
    ).all()
    
    if len(tech_stacks) != len(tech_stack_update.tech_stack_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some tech stack IDs are invalid"
        )
    
    # Update user's tech stacks
    current_user.tech_stacks = tech_stacks
    db.commit()
    
    return {
        "message": "Tech stack updated successfully",
        "tech_stacks": tech_stacks
    }

@router.delete("/my-stack/{tech_stack_id}")
async def remove_tech_stack_from_user(
    tech_stack_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a tech stack from current user"""
    # Find the tech stack
    tech_stack = db.query(TechStack).filter(TechStack.id == tech_stack_id).first()
    if not tech_stack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tech stack not found"
        )
    
    # Remove from user's tech stacks
    if tech_stack in current_user.tech_stacks:
        current_user.tech_stacks.remove(tech_stack)
        db.commit()
        return {"message": "Tech stack removed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tech stack not in user's stack"
        )