"""
Multi-Agent Chatbot - FastAPI REST API Server
Provides REST endpoints for multi-agent conversations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime
import uuid

import sys
sys.path.append('/app')
from playbooks.multi_agent_chatbot.orchestration import MultiAgentChatbot

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== Request/Response Models =====

class ChatMessage(BaseModel):
    """Request model for chat"""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (auto-generated if not provided)")
    use_coordination: bool = Field(True, description="Whether to use multi-agent coordination")


class ChatResponse(BaseModel):
    """Response model for chat"""
    response: str = Field(..., description="Agent response")
    conversation_id: str = Field(..., description="Conversation ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")


class ConversationInfo(BaseModel):
    """Conversation information"""
    conversation_id: str
    message_count: int
    created_at: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    num_agents: int
    active_conversations: int


# ===== FastAPI Application =====

app = FastAPI(
    title="Multi-Agent Chatbot API",
    description="Orchestrated multi-agent conversational system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Global State =====

chatbot = None


# ===== API Endpoints =====

@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup"""
    global chatbot
    logger.info("Initializing Multi-Agent Chatbot...")
    chatbot = MultiAgentChatbot(
        llm_url="http://agent4:8000",
        port=8080
    )
    logger.info(f"Chatbot initialized with {len(chatbot.agents)} agents")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "num_agents": len(chatbot.agents) if chatbot else 0,
        "active_conversations": len(chatbot.conversations) if chatbot else 0
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Chat endpoint - MAIN ENDPOINT FOR FUNCTIONAL TEST

    Send a message and get a response from the multi-agent system.
    """
    try:
        # Generate conversation ID if not provided
        if message.conversation_id is None:
            message.conversation_id = f"conv_{uuid.uuid4().hex[:16]}"

        # Process message
        result = await chatbot.chat(
            user_input=message.message,
            conversation_id=message.conversation_id,
            use_coordination=message.use_coordination
        )

        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            metadata=result["metadata"]
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations")
async def list_conversations():
    """List all active conversations"""
    conversations = []
    for conv_id, context in chatbot.conversations.items():
        conversations.append({
            "conversation_id": conv_id,
            "message_count": len(context.messages),
            "created_at": context.created_at.isoformat()
        })
    return {"conversations": conversations}


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    context = chatbot.get_conversation(conversation_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = [
        {
            "id": msg.id,
            "type": msg.type.value,
            "sender": msg.sender,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in context.messages
    ]

    return {
        "conversation_id": conversation_id,
        "message_count": len(messages),
        "created_at": context.created_at.isoformat(),
        "messages": messages
    }


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id in chatbot.conversations:
        del chatbot.conversations[conversation_id]
        return {"status": "success", "message": f"Conversation {conversation_id} deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")


@app.get("/agents")
async def list_agents():
    """List all available agents"""
    return {"agents": chatbot.get_agent_info()}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Multi-Agent Chatbot",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "num_agents": len(chatbot.agents) if chatbot else 0
    }


# ===== Main Entry Point =====

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
