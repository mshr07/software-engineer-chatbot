from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, InterviewQuestion
from app.schemas import (
    InterviewQuestionRequest, InterviewQuestionResponse, 
    InterviewQuestionSet
)
from app.auth import get_current_active_user
from app.services.openai_service import openai_service

router = APIRouter()

async def generate_interview_questions_with_ai(
    years_of_experience: int,
    target_role: str,
    tech_stack: List[str],
    focus_areas: List[str],
    num_questions: int
) -> List[Dict[str, Any]]:
    """Generate interview questions using OpenAI based on user profile"""
    
    # Determine experience level
    if years_of_experience <= 2:
        experience_level = "Junior"
    elif years_of_experience <= 5:
        experience_level = "Mid-level"
    elif years_of_experience <= 10:
        experience_level = "Senior"
    else:
        experience_level = "Lead/Principal"
    
    tech_stack_str = ", ".join(tech_stack) if tech_stack else "General software engineering"
    focus_areas_str = ", ".join(focus_areas) if focus_areas else "General technical and behavioral"
    
    system_prompt = f"""
You are an expert technical interviewer who creates realistic interview questions for software engineering positions.

Generate exactly {num_questions} interview questions for:
- Target Role: {target_role}
- Experience Level: {experience_level} ({years_of_experience} years)
- Tech Stack: {tech_stack_str}
- Focus Areas: {focus_areas_str}

For each question, provide:
1. The question text
2. Category (Technical, System Design, Behavioral, Coding, or Problem Solving)
3. Difficulty level appropriate for {experience_level}
4. A brief expected answer or key points to look for

Questions should be:
- Appropriate for the experience level
- Relevant to the target role and tech stack
- Mix of technical and behavioral questions
- Realistic and commonly asked in actual interviews
- Progressively challenging within the experience level

Format your response as a JSON array where each question is an object with these fields:
- "question": the question text
- "category": one of "Technical", "System Design", "Behavioral", "Coding", "Problem Solving"
- "difficulty_level": "{experience_level}"
- "tech_stack": relevant technology (or null if general)
- "expected_answer": brief guidance on what to look for in answers

Respond ONLY with valid JSON, no additional text.
"""
    
    try:
        response = await openai_service.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt}
            ],
            max_tokens=2000,
            temperature=0.8
        )
        
        import json
        questions_data = json.loads(response.choices[0].message.content)
        return questions_data
        
    except Exception as e:
        # Fallback questions if AI generation fails
        fallback_questions = [
            {
                "question": f"Tell me about a challenging {tech_stack_str} project you worked on.",
                "category": "Behavioral",
                "difficulty_level": experience_level,
                "tech_stack": tech_stack_str,
                "expected_answer": "Look for specific examples, problem-solving approach, and lessons learned."
            },
            {
                "question": f"How would you optimize the performance of a {tech_stack_str} application?",
                "category": "Technical",
                "difficulty_level": experience_level,
                "tech_stack": tech_stack_str,
                "expected_answer": "Performance monitoring, caching strategies, database optimization, code profiling."
            },
            {
                "question": "Describe your approach to code review and maintaining code quality.",
                "category": "Behavioral",
                "difficulty_level": experience_level,
                "tech_stack": None,
                "expected_answer": "Code standards, testing practices, constructive feedback, knowledge sharing."
            }
        ]
        return fallback_questions[:num_questions]

@router.post("/generate", response_model=InterviewQuestionSet)
async def generate_interview_questions(
    request: InterviewQuestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate interview questions based on user profile and requirements"""
    
    # Get user's tech stack
    user_tech_stack = [tech.name for tech in current_user.tech_stacks]
    
    # If no focus areas specified, use user's tech stack
    focus_areas = request.focus_areas if request.focus_areas else user_tech_stack[:5]
    
    # Generate questions using AI
    questions_data = await generate_interview_questions_with_ai(
        years_of_experience=request.years_of_experience,
        target_role=request.target_role,
        tech_stack=user_tech_stack,
        focus_areas=focus_areas,
        num_questions=request.num_questions
    )
    
    # Save generated questions to database
    generated_questions = []
    for q_data in questions_data:
        # Check if similar question already exists
        existing = db.query(InterviewQuestion).filter(
            InterviewQuestion.question == q_data["question"]
        ).first()
        
        if not existing:
            interview_question = InterviewQuestion(
                question=q_data["question"],
                category=q_data["category"],
                difficulty_level=q_data["difficulty_level"],
                tech_stack=q_data.get("tech_stack"),
                expected_answer=q_data.get("expected_answer")
            )
            db.add(interview_question)
            db.commit()
            db.refresh(interview_question)
            generated_questions.append(interview_question)
        else:
            generated_questions.append(existing)
    
    user_context = {
        "years_of_experience": request.years_of_experience,
        "target_role": request.target_role,
        "tech_stack": user_tech_stack,
        "focus_areas": focus_areas,
        "current_role": current_user.current_role,
        "username": current_user.username
    }
    
    return InterviewQuestionSet(
        questions=generated_questions,
        user_context=user_context
    )

@router.get("/saved", response_model=List[InterviewQuestionResponse])
async def get_saved_interview_questions(
    category: str = None,
    difficulty_level: str = None,
    tech_stack: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get saved interview questions with optional filters"""
    
    query = db.query(InterviewQuestion)
    
    if category:
        query = query.filter(InterviewQuestion.category == category)
    if difficulty_level:
        query = query.filter(InterviewQuestion.difficulty_level == difficulty_level)
    if tech_stack:
        query = query.filter(InterviewQuestion.tech_stack.contains(tech_stack))
    
    questions = query.order_by(InterviewQuestion.created_at.desc()).limit(limit).all()
    return questions

@router.get("/categories")
async def get_question_categories(db: Session = Depends(get_db)):
    """Get all available question categories"""
    categories = db.query(InterviewQuestion.category).distinct().all()
    return {"categories": [cat[0] for cat in categories if cat[0]]}

@router.get("/difficulty-levels")
async def get_difficulty_levels():
    """Get all available difficulty levels"""
    return {
        "difficulty_levels": ["Junior", "Mid-level", "Senior", "Lead/Principal"]
    }

@router.post("/practice-set")
async def generate_practice_interview_set(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a practice interview set based on user's current profile"""
    
    # Use user's current experience and role for practice
    years_exp = current_user.years_of_experience or 3
    target_role = current_user.current_role or "Software Engineer"
    
    request = InterviewQuestionRequest(
        years_of_experience=years_exp,
        target_role=target_role,
        focus_areas=[],
        num_questions=10
    )
    
    return await generate_interview_questions(request, current_user, db)

@router.get("/stats")
async def get_interview_question_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get statistics about available interview questions"""
    
    total_questions = db.query(InterviewQuestion).count()
    
    categories_count = db.query(
        InterviewQuestion.category, 
        db.func.count(InterviewQuestion.id)
    ).group_by(InterviewQuestion.category).all()
    
    difficulty_count = db.query(
        InterviewQuestion.difficulty_level,
        db.func.count(InterviewQuestion.id)
    ).group_by(InterviewQuestion.difficulty_level).all()
    
    user_tech_count = 0
    if current_user.tech_stacks:
        user_tech_names = [tech.name for tech in current_user.tech_stacks]
        for tech in user_tech_names:
            count = db.query(InterviewQuestion).filter(
                InterviewQuestion.tech_stack.contains(tech)
            ).count()
            user_tech_count += count
    
    return {
        "total_questions": total_questions,
        "categories": dict(categories_count),
        "difficulty_levels": dict(difficulty_count),
        "relevant_to_user_tech_stack": user_tech_count,
        "user_tech_stack": [tech.name for tech in current_user.tech_stacks]
    }