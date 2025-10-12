#!/usr/bin/env python3
"""
Database initialization script
This script creates the database tables and populates initial data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import engine, Base
from app.models import TechStack
from app.database import SessionLocal

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")

def enable_pgvector():
    """Enable pgvector extension in PostgreSQL"""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        print("✓ pgvector extension enabled")
    except Exception as e:
        print(f"Warning: Could not enable pgvector extension: {e}")
        print("Make sure PostgreSQL has the pgvector extension installed")

def populate_tech_stacks():
    """Populate initial tech stack data"""
    print("Populating tech stacks...")
    
    db = SessionLocal()
    
    tech_stacks = [
        # Programming Languages
        {"name": "Python", "category": "Programming Language", "description": "High-level programming language for general-purpose programming"},
        {"name": "JavaScript", "category": "Programming Language", "description": "Dynamic programming language for web development"},
        {"name": "TypeScript", "category": "Programming Language", "description": "Typed superset of JavaScript"},
        {"name": "Java", "category": "Programming Language", "description": "Object-oriented programming language"},
        {"name": "C#", "category": "Programming Language", "description": "Microsoft's object-oriented programming language"},
        {"name": "C++", "category": "Programming Language", "description": "General-purpose programming language"},
        {"name": "Go", "category": "Programming Language", "description": "Programming language developed by Google"},
        {"name": "Rust", "category": "Programming Language", "description": "Systems programming language focused on safety"},
        {"name": "Ruby", "category": "Programming Language", "description": "Dynamic programming language"},
        {"name": "PHP", "category": "Programming Language", "description": "Server-side scripting language"},
        {"name": "Swift", "category": "Programming Language", "description": "Apple's programming language for iOS/macOS"},
        {"name": "Kotlin", "category": "Programming Language", "description": "JVM programming language by JetBrains"},
        
        # Web Frameworks
        {"name": "React", "category": "Frontend Framework", "description": "JavaScript library for building user interfaces"},
        {"name": "Angular", "category": "Frontend Framework", "description": "TypeScript-based web application framework"},
        {"name": "Vue.js", "category": "Frontend Framework", "description": "Progressive JavaScript framework"},
        {"name": "Svelte", "category": "Frontend Framework", "description": "Compile-time web framework"},
        {"name": "Next.js", "category": "Frontend Framework", "description": "React framework for production"},
        
        # Backend Frameworks
        {"name": "Node.js", "category": "Backend Framework", "description": "JavaScript runtime for server-side development"},
        {"name": "Express.js", "category": "Backend Framework", "description": "Fast web framework for Node.js"},
        {"name": "FastAPI", "category": "Backend Framework", "description": "Modern Python web framework"},
        {"name": "Django", "category": "Backend Framework", "description": "High-level Python web framework"},
        {"name": "Flask", "category": "Backend Framework", "description": "Lightweight Python web framework"},
        {"name": "Spring Boot", "category": "Backend Framework", "description": "Java framework for building applications"},
        {"name": "ASP.NET Core", "category": "Backend Framework", "description": "Microsoft's web framework"},
        {"name": "Ruby on Rails", "category": "Backend Framework", "description": "Ruby web framework"},
        
        # Databases
        {"name": "PostgreSQL", "category": "Database", "description": "Advanced open-source relational database"},
        {"name": "MySQL", "category": "Database", "description": "Popular open-source relational database"},
        {"name": "MongoDB", "category": "Database", "description": "Document-oriented NoSQL database"},
        {"name": "Redis", "category": "Database", "description": "In-memory data structure store"},
        {"name": "SQLite", "category": "Database", "description": "Lightweight relational database"},
        {"name": "Cassandra", "category": "Database", "description": "Distributed NoSQL database"},
        {"name": "Elasticsearch", "category": "Database", "description": "Search and analytics engine"},
        
        # Cloud Platforms
        {"name": "AWS", "category": "Cloud Platform", "description": "Amazon Web Services"},
        {"name": "Google Cloud", "category": "Cloud Platform", "description": "Google Cloud Platform"},
        {"name": "Azure", "category": "Cloud Platform", "description": "Microsoft Azure"},
        {"name": "Heroku", "category": "Cloud Platform", "description": "Platform as a service"},
        {"name": "Vercel", "category": "Cloud Platform", "description": "Frontend deployment platform"},
        
        # DevOps Tools
        {"name": "Docker", "category": "DevOps", "description": "Containerization platform"},
        {"name": "Kubernetes", "category": "DevOps", "description": "Container orchestration platform"},
        {"name": "Jenkins", "category": "DevOps", "description": "Automation server for CI/CD"},
        {"name": "GitHub Actions", "category": "DevOps", "description": "CI/CD platform by GitHub"},
        {"name": "Terraform", "category": "DevOps", "description": "Infrastructure as code tool"},
        {"name": "Ansible", "category": "DevOps", "description": "Configuration management tool"},
        
        # Mobile Development
        {"name": "React Native", "category": "Mobile Framework", "description": "Cross-platform mobile development"},
        {"name": "Flutter", "category": "Mobile Framework", "description": "Google's UI toolkit for mobile"},
        {"name": "Ionic", "category": "Mobile Framework", "description": "Hybrid mobile app framework"},
        {"name": "Xamarin", "category": "Mobile Framework", "description": "Microsoft's cross-platform framework"},
        
        # Testing
        {"name": "Jest", "category": "Testing", "description": "JavaScript testing framework"},
        {"name": "Pytest", "category": "Testing", "description": "Python testing framework"},
        {"name": "JUnit", "category": "Testing", "description": "Java testing framework"},
        {"name": "Cypress", "category": "Testing", "description": "End-to-end testing framework"},
        {"name": "Selenium", "category": "Testing", "description": "Web application testing framework"},
        
        # Tools
        {"name": "Git", "category": "Version Control", "description": "Distributed version control system"},
        {"name": "GitHub", "category": "Version Control", "description": "Git repository hosting service"},
        {"name": "GitLab", "category": "Version Control", "description": "DevOps platform with Git repository"},
        {"name": "Jira", "category": "Project Management", "description": "Issue tracking and project management"},
        {"name": "Confluence", "category": "Documentation", "description": "Team collaboration software"},
        
        # AI/ML
        {"name": "TensorFlow", "category": "Machine Learning", "description": "Machine learning platform"},
        {"name": "PyTorch", "category": "Machine Learning", "description": "Machine learning library"},
        {"name": "Scikit-learn", "category": "Machine Learning", "description": "Machine learning library for Python"},
        {"name": "OpenAI API", "category": "AI/ML", "description": "API for AI language models"},
        {"name": "Hugging Face", "category": "AI/ML", "description": "Platform for machine learning models"},
    ]
    
    added_count = 0
    for tech_data in tech_stacks:
        existing = db.query(TechStack).filter(TechStack.name == tech_data["name"]).first()
        if not existing:
            tech_stack = TechStack(**tech_data)
            db.add(tech_stack)
            added_count += 1
    
    db.commit()
    db.close()
    
    print(f"✓ Added {added_count} tech stacks to database")

def main():
    print("Initializing database...")
    
    try:
        enable_pgvector()
        create_tables()
        populate_tech_stacks()
        
        print("\n✅ Database initialization completed successfully!")
        print("\nYou can now start the application with:")
        print("uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())