# Software Engineer Chatbot

An AI-powered chatbot specifically designed for software engineers, featuring personalized tech stack management, context-aware responses, and interview question generation.

## Features

🤖 **AI-Powered Chat Assistant**
- OpenAI-powered responses tailored to software engineering topics
- Context-aware responses based on your tech stack
- Restricted to software engineering queries for focused assistance

🛠️ **Tech Stack Management**
- Update and manage your technology preferences
- Personalized responses based on your skills
- Support for 60+ technologies across multiple categories

📝 **Interview Question Generation**
- Generate questions based on years of experience
- Tailored to your tech stack and target role
- Practice sets for interview preparation

💾 **Data Persistence**
- Chat history stored with session management
- User profiles with experience tracking
- PostgreSQL with pgvector for semantic search

🔒 **Security Features**
- JWT-based authentication
- Rate limiting to prevent abuse
- Input validation and security headers

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- PostgreSQL with pgvector extension
- SQLAlchemy ORM
- OpenAI API integration

**Frontend:**
- HTML5 + Tailwind CSS
- Vanilla JavaScript
- Responsive design

**Security:**
- JWT tokens for authentication
- Rate limiting middleware
- Security headers and CORS protection

## Prerequisites

Before running the application, ensure you have:

1. **Python 3.8+** installed
2. **PostgreSQL** with **pgvector** extension
3. **OpenAI API Key** (the one provided in your request)
4. **Redis** (optional, for caching)

## Installation & Setup

### 1. Clone and Setup Environment

```bash
# Create project directory (already done)
cd software-engineer-chatbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

**Install PostgreSQL and pgvector:**

```bash
# On macOS with Homebrew
brew install postgresql pgvector

# Start PostgreSQL
brew services start postgresql

# Create database
createdb chatbot_db
```

**For other systems, install pgvector:**
```sql
-- Connect to your PostgreSQL database and run:
CREATE EXTENSION vector;
```

### 3. Environment Configuration

The `.env` file is already created with your OpenAI API key. Update the database URL:

```bash
# Update .env file
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/chatbot_db
SECRET_KEY=your-secret-key-change-in-production
```

### 4. Initialize Database

```bash
# Run the database initialization script
python scripts/init_db.py
```

This will:
- Create all database tables
- Enable pgvector extension
- Populate 60+ tech stack options

### 5. Run the Application

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The application will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

## Key API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info

### Tech Stack Management  
- `GET /api/techstack/available` - Get available technologies
- `GET /api/techstack/my-stack` - Get user's tech stack
- `PUT /api/techstack/my-stack` - Update user's tech stack

### Chat Interface
- `POST /api/chat/session` - Create new chat session
- `POST /api/chat/message` - Send message and get AI response
- `GET /api/chat/sessions` - Get user's chat sessions
- `POST /api/chat/history` - Get chat history by username/session

### Interview Questions
- `POST /api/interview/generate` - Generate custom interview questions
- `POST /api/interview/practice-set` - Get practice interview set
- `GET /api/interview/saved` - Get saved questions with filters

## Usage Guide

### 1. Register/Login
- Create an account with your programming experience
- Login to access the full features

### 2. Setup Tech Stack
- Navigate to the Tech Stack section
- Select your programming languages, frameworks, databases, etc.
- This personalizes your AI responses

### 3. Chat with AI
- Ask questions about programming, debugging, system design
- Get responses tailored to your tech stack
- Chat history is automatically saved

### 4. Generate Interview Questions
- Click "Generate Questions" for custom interview prep
- Specify target role and experience level
- Get questions based on your tech stack

## Deployment

### Docker Deployment (Recommended)

```bash
# Create Dockerfile
cat > Dockerfile << EOF
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Build and run
docker build -t software-engineer-chatbot .
docker run -p 8000:8000 --env-file .env software-engineer-chatbot
```

### Cloud Deployment

The application is ready for deployment on:
- **Heroku**: Add `Procfile` with `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Railway**: Connect your GitHub repo and deploy
- **Google Cloud Run**: Use the provided Docker configuration
- **AWS ECS/Fargate**: Deploy with the Docker image

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `ALGORITHM` | JWT algorithm (HS256) | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration (30) | No |
| `REDIS_URL` | Redis connection URL | No |

## Security Features

- **Authentication**: JWT-based with secure password hashing
- **Rate Limiting**: API calls limited per IP address
- **Input Validation**: All inputs validated with Pydantic
- **SQL Injection Protection**: SQLAlchemy ORM prevents injection
- **CORS Protection**: Configurable allowed origins
- **Security Headers**: XSS, CSP, and other security headers

## Monitoring and Logging

The application includes:
- Request/response logging
- Error tracking with stack traces
- Health check endpoint (`/health`)
- Database connection monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Troubleshooting

**Database Connection Issues:**
```bash
# Check PostgreSQL is running
pg_ctl status

# Check if database exists
psql -l | grep chatbot_db
```

**OpenAI API Issues:**
- Verify API key is correct in `.env`
- Check API quota and billing
- Monitor rate limits in logs

**pgvector Issues:**
```sql
-- Verify extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## Support

For issues or questions:
1. Check the logs: `tail -f app.log`
2. Review the API documentation at `/docs`
3. Check database connectivity with `/health`

---

🚀 **Your AI-powered software engineering assistant is ready to help with coding questions, technical problems, and interview preparation!**