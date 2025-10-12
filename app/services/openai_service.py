import openai
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = settings.openai_api_key

class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def is_software_engineering_query(self, query: str) -> bool:
        """Check if the query is related to software engineering"""
        system_prompt = """
        You are a classifier that determines if a query is related to software engineering.
        Software engineering topics include: programming languages, frameworks, databases, 
        system design, algorithms, data structures, debugging, code review, testing, 
        deployment, DevOps, cloud computing, software architecture, design patterns,
        version control, API development, web development, mobile development,
        machine learning engineering, and career advice for software engineers.
        
        Respond with only "YES" if the query is related to software engineering,
        or "NO" if it's not related to software engineering.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=5,
                temperature=0
            )
            
            answer = response.choices[0].message.content.strip().upper()
            return answer == "YES"
        except Exception as e:
            logger.error(f"Error checking if query is software engineering related: {e}")
            # If we can't determine, err on the side of caution and allow it
            return True
    
    async def generate_chat_response(
        self, 
        query: str, 
        user_tech_stack: List[Dict[str, Any]], 
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate a chat response based on user query and tech stack context"""
        
        # First check if the query is software engineering related
        if not await self.is_software_engineering_query(query):
            return ("I'm a specialized chatbot for software engineering topics. "
                   "I can help with programming languages, frameworks, system design, "
                   "debugging, career advice for developers, and other software engineering topics. "
                   "Please ask me something related to software development!")
        
        # Build context from user's tech stack
        tech_context = ""
        if user_tech_stack:
            tech_names = [tech['name'] for tech in user_tech_stack]
            tech_categories = {}
            for tech in user_tech_stack:
                category = tech['category']
                if category not in tech_categories:
                    tech_categories[category] = []
                tech_categories[category].append(tech['name'])
            
            tech_context = f"""
User's Tech Stack:
{', '.join(tech_names)}

Categorized:
"""
            for category, techs in tech_categories.items():
                tech_context += f"- {category}: {', '.join(techs)}\n"
        
        # Build system prompt
        system_prompt = f"""
You are an expert software engineering assistant specialized in helping software engineers 
with technical questions, debugging, best practices, and career advice.

IMPORTANT RULES:
1. Only answer questions related to software engineering, programming, and technology
2. If asked about non-technical topics, politely redirect to software engineering topics
3. Provide practical, actionable advice
4. Consider the user's tech stack when giving recommendations
5. Be concise but comprehensive
6. Include code examples when relevant
7. Suggest best practices and potential pitfalls

{tech_context}

When providing answers:
- Tailor responses to the user's known technologies when relevant
- Provide code examples in the user's preferred languages/frameworks when possible
- Suggest alternatives that align with their tech stack
- Be encouraging and educational
"""
        
        # Build conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_history:
            # Add recent chat history (last 10 messages to stay within token limits)
            recent_history = chat_history[-10:]
            for msg in recent_history:
                messages.append({
                    "role": msg["message_type"], 
                    "content": msg["content"]
                })
        
        messages.append({"role": "user", "content": query})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return ("I'm experiencing some technical difficulties right now. "
                   "Please try again in a moment, or rephrase your question.")
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text using OpenAI's embedding model"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    async def search_similar_messages(
        self, 
        query_embedding: List[float],
        stored_embeddings: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar messages using cosine similarity (simplified version)"""
        # This is a basic implementation. In production, you'd use a proper vector database
        # like pgvector with proper similarity search
        
        if not query_embedding or not stored_embeddings:
            return []
        
        similarities = []
        for stored in stored_embeddings:
            if not stored.get('embedding'):
                continue
            
            # Simple dot product similarity (assuming normalized vectors)
            similarity = sum(a * b for a, b in zip(query_embedding, stored['embedding']))
            similarities.append({
                'similarity': similarity,
                'message': stored
            })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return [item['message'] for item in similarities[:limit]]

# Create a singleton instance
openai_service = OpenAIService()