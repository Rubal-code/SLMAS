# SLMAS-DigitalOcean

Self-Learning AI Agent MVP

## Overview
This project is a lightweight self-learning AI agent backend built in Python with FastAPI.

It includes:
- task creation and persistence
- Groq-ready planning adapter
- execution engine with mock tools
- learning memory for prior tasks
- evaluator and learning export
- admin approval and feedback endpoints

## Quick start

1. Copy environment example:
   copy .env.example .env

2. Fill Groq settings in .env:
   GROQ_API_KEY=your_key
   GROQ_API_URL=https://api.groq.com/openai/v1
   GROQ_MODEL=llama-3.3-70b-versatile

3. Install dependencies:
   pip install -r requirements.txt

4. Start the app:
   uvicorn app.main:app --reload

5. Check the health endpoint:
   http://localhost:8000/health

## API examples

Create task:
POST /tasks
{
  "goal_text": "Build a self-learning AI agent"
}

Get task:
GET /tasks/{task_id}

Execute task:
POST /tasks/{task_id}/execute

Admin feedback:
POST /admin/feedback
{
  "task_id": "<task_id>",
  "rating": 5,
  "notes": "Looks good"
}

Admin approval:
POST /admin/approve
{
  "action": "delete_user",
  "approved": false,
  "reason": "Safety review"
}

## Notes
- Phase 0+ phases are implemented incrementally
- SQLite is used for MVP persistence
- Groq is default LLM for the planning layer
- Local memory is used before production vector DB is introduced
