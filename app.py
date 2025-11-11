"""
Aurora Chatbot - Improved Question Answering System
This version includes better context management and user filtering
"""
import os
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Aurora QA System v2",
    description="Improved question-answering system for member data",
    version="2.0.0"
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
MESSAGES_API_URL = os.getenv(
    "MESSAGES_API_URL",
    "https://november7-730026606190.europe-west1.run.app/messages/"
)


class QuestionRequest(BaseModel):
    """Request model for the /ask endpoint"""
    question: str = Field(..., description="Natural language question about member data")


class AnswerResponse(BaseModel):
    """Response model for the /ask endpoint"""
    answer: str = Field(..., description="Answer to the question")


class MessageCache:
    """Simple cache for messages"""
    def __init__(self):
        self.messages: Optional[List[Dict[str, Any]]] = None
        self.last_updated: Optional[datetime] = None
        self.cache_duration_seconds = 300

    def is_valid(self) -> bool:
        if self.messages is None or self.last_updated is None:
            return False
        age = (datetime.now() - self.last_updated).total_seconds()
        return age < self.cache_duration_seconds

    def set(self, messages: List[Dict[str, Any]]):
        self.messages = messages
        self.last_updated = datetime.now()

    def get(self) -> Optional[List[Dict[str, Any]]]:
        if self.is_valid():
            return self.messages
        return None


message_cache = MessageCache()


async def fetch_all_messages() -> List[Dict[str, Any]]:
    """Fetch all messages from the API with pagination."""
    cached_messages = message_cache.get()
    if cached_messages is not None:
        return cached_messages

    messages = []
    skip = 0
    limit = 1000

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                response = await client.get(
                    MESSAGES_API_URL,
                    params={"skip": skip, "limit": limit},
                    follow_redirects=True
                )
                response.raise_for_status()
                data = response.json()

                items = data.get("items", [])
                if not items:
                    break

                messages.extend(items)

                if len(messages) >= data.get("total", 0):
                    break

                skip += limit

            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch messages from API: {str(e)}"
                )

    message_cache.set(messages)
    return messages


def extract_user_names(question: str) -> List[str]:
    """
    Extract potential user names from the question.
    Returns list of capitalized name patterns found.
    """
    # Common first names in the dataset
    known_users = [
        "Layla", "Vikram", "Amira", "Sophia", "Fatima",
        "Armand", "Hans", "Lorenzo", "Lily", "Thiago", "Amina"
    ]

    found_names = []
    question_lower = question.lower()

    for name in known_users:
        if name.lower() in question_lower:
            found_names.append(name)

    return found_names


def filter_messages_by_user(messages: List[Dict[str, Any]], user_names: List[str]) -> List[Dict[str, Any]]:
    """
    Filter messages to only include specific users.
    Uses fuzzy matching to handle name variations.
    """
    if not user_names:
        return messages

    filtered = []
    for msg in messages:
        msg_user = msg["user_name"]
        for query_name in user_names:
            if query_name.lower() in msg_user.lower():
                filtered.append(msg)
                break

    return filtered


def create_context_from_messages(messages: List[Dict[str, Any]], max_messages: int = 500) -> str:
    """
    Create context from messages, limiting total size.
    Groups by user and takes recent messages.
    """
    # Group by user
    user_messages: Dict[str, List[str]] = {}
    for msg in messages:
        user_name = msg["user_name"]
        message_text = msg["message"]
        timestamp = msg["timestamp"]

        if user_name not in user_messages:
            user_messages[user_name] = []

        user_messages[user_name].append(f"[{timestamp[:10]}] {message_text}")

    # Build context
    context_parts = []
    total_messages = 0

    for user_name, msgs in sorted(user_messages.items()):
        context_parts.append(f"\n=== {user_name} ===")
        # Take all messages if filtered, or limit if full dataset
        msgs_to_include = msgs if len(messages) < 200 else msgs[:50]
        for msg in msgs_to_include:
            context_parts.append(msg)
            total_messages += 1
            if total_messages >= max_messages:
                break
        if total_messages >= max_messages:
            break

    return "\n".join(context_parts)


async def answer_question_with_llm(question: str, messages: List[Dict[str, Any]]) -> str:
    """
    Use OpenAI's GPT to answer questions.
    Filters messages by user if mentioned in question.
    """
    # Extract user names from question
    user_names = extract_user_names(question)

    # Filter messages if user mentioned
    if user_names:
        filtered_messages = filter_messages_by_user(messages, user_names)
        if filtered_messages:
            print(f"Filtered to {len(filtered_messages)} messages for users: {user_names}")
            messages = filtered_messages
        else:
            print(f"Warning: No messages found for users: {user_names}")

    # Create context
    context = create_context_from_messages(messages)

    # Prepare prompt
    system_prompt = """You are a helpful assistant answering questions about luxury concierge service members.

Key rules:
- Answer based ONLY on the messages provided
- Be specific: include dates, locations, preferences when available
- If a user name in the question doesn't exist, mention which similar names ARE available
- List multiple relevant details when found
- If truly no information exists, say so clearly"""

    user_prompt = f"""Question: {question}

Member Messages:
{context}

Provide a helpful answer based on the messages above."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        answer = response.choices[0].message.content.strip()
        return answer

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calling OpenAI API: {str(e)}"
        )


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "service": "Aurora QA System v2",
        "version": "2.0.0",
        "improvements": "Better context filtering and user extraction"
    }


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest) -> AnswerResponse:
    """Answer a natural language question about member data."""
    messages = await fetch_all_messages()
    answer = await answer_question_with_llm(request.question, messages)
    return AnswerResponse(answer=answer)


@app.get("/stats")
async def get_stats():
    """Get dataset statistics"""
    messages = await fetch_all_messages()
    users = {}
    for msg in messages:
        user_name = msg["user_name"]
        if user_name not in users:
            users[user_name] = 0
        users[user_name] += 1

    return {
        "total_messages": len(messages),
        "unique_users": len(users),
        "users": users
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))  # Different port to avoid conflict
    uvicorn.run(app, host=host, port=port)
