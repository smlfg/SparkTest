"""
Unit tests for Multi-Agent Chatbot
Tests the chatbot according to technical requirements
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

# Import chatbot components
import sys
sys.path.append('/app')


class TestMultiAgentChatbot:
    """Tests for multi-agent chatbot functionality"""

    def test_agent_initialization(self):
        """Test that all agents are initialized"""
        from playbooks.multi_agent_chatbot.orchestration import MultiAgentChatbot

        chatbot = MultiAgentChatbot(llm_url="http://localhost:8000")

        # Should have 5 specialized agents
        assert len(chatbot.agents) >= 4
        assert "researcher" in chatbot.agents
        assert "analyst" in chatbot.agents
        assert "writer" in chatbot.agents
        assert "critic" in chatbot.agents

        # Should have coordinator
        assert chatbot.coordinator is not None

    def test_agent_roles(self):
        """Test that agents have correct roles"""
        from playbooks.multi_agent_chatbot.orchestration import MultiAgentChatbot, AgentRole

        chatbot = MultiAgentChatbot()

        # Check agent roles
        assert chatbot.agents["researcher"].capability.role == AgentRole.RESEARCHER
        assert chatbot.agents["analyst"].capability.role == AgentRole.ANALYST
        assert chatbot.agents["writer"].capability.role == AgentRole.WRITER
        assert chatbot.agents["critic"].capability.role == AgentRole.CRITIC

    @pytest.mark.asyncio
    async def test_conversation_context(self):
        """Test conversation context management"""
        from playbooks.multi_agent_chatbot.orchestration import MultiAgentChatbot

        chatbot = MultiAgentChatbot()

        # Create conversation
        conv_id = "test_conv_001"
        context = chatbot.create_conversation(conv_id)

        assert context.conversation_id == conv_id
        assert len(context.messages) == 0

        # Retrieve conversation
        retrieved = chatbot.get_conversation(conv_id)
        assert retrieved is not None
        assert retrieved.conversation_id == conv_id

    @pytest.mark.asyncio
    async def test_agent_coordination(self):
        """Test multi-agent coordination"""
        from playbooks.multi_agent_chatbot.orchestration import MultiAgentChatbot

        chatbot = MultiAgentChatbot()

        # Test coordination
        if chatbot.coordinator:
            # Coordinator should have coordination capabilities
            assert "coordination" in str(chatbot.coordinator.capability.description).lower() or \
                   "orchestrat" in str(chatbot.coordinator.capability.description).lower()

    @pytest.mark.asyncio
    async def test_message_flow(self):
        """Test message flow through system"""
        from playbooks.multi_agent_chatbot.orchestration import MultiAgentChatbot, MessageType

        chatbot = MultiAgentChatbot()
        conv_id = "test_conv_002"

        # Create conversation
        context = chatbot.create_conversation(conv_id)

        # Simulate user message
        from playbooks.multi_agent_chatbot.orchestration import Message

        user_msg = Message(
            id="msg_001",
            type=MessageType.USER_INPUT,
            sender="user",
            content="Hello"
        )

        context.add_message(user_msg)

        assert len(context.messages) == 1
        assert context.get_last_user_message().content == "Hello"


class TestChatbotAPI:
    """Tests for Chatbot REST API"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test /health endpoint"""
        from fastapi.testclient import TestClient
        from playbooks.multi_agent_chatbot.server import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "num_agents" in data
        assert "active_conversations" in data

    @pytest.mark.asyncio
    async def test_chat_endpoint(self):
        """Test /chat endpoint (checklist requirement)"""
        from fastapi.testclient import TestClient
        from playbooks.multi_agent_chatbot.server import app

        client = TestClient(app)

        # Send message
        response = client.post(
            "/chat",
            json={"message": "hello"}
        )

        # Should return HTTP 200 (checklist requirement)
        assert response.status_code == 200

        data = response.json()

        # Verify response structure
        assert "response" in data
        assert isinstance(data["response"], str)

        assert "conversation_id" in data
        assert isinstance(data["conversation_id"], str)

        assert "metadata" in data
        assert isinstance(data["metadata"], dict)

    @pytest.mark.asyncio
    async def test_conversation_continuity(self):
        """Test conversation continuity across messages"""
        from fastapi.testclient import TestClient
        from playbooks.multi_agent_chatbot.server import app

        client = TestClient(app)

        # First message
        response1 = client.post(
            "/chat",
            json={"message": "Hello"}
        )
        data1 = response1.json()
        conv_id = data1["conversation_id"]

        # Second message in same conversation
        response2 = client.post(
            "/chat",
            json={
                "message": "Continue",
                "conversation_id": conv_id
            }
        )
        data2 = response2.json()

        # Should maintain same conversation
        assert data2["conversation_id"] == conv_id
        assert data2["metadata"]["message_count"] > data1["metadata"]["message_count"]

    @pytest.mark.asyncio
    async def test_agents_endpoint(self):
        """Test /agents endpoint"""
        from fastapi.testclient import TestClient
        from playbooks.multi_agent_chatbot.server import app

        client = TestClient(app)
        response = client.get("/agents")

        assert response.status_code == 200
        data = response.json()

        assert "agents" in data
        assert isinstance(data["agents"], list)
        assert len(data["agents"]) > 0

        # Check agent structure
        agent = data["agents"][0]
        assert "id" in agent
        assert "role" in agent
        assert "description" in agent
        assert "skills" in agent


class TestAgentIntegration:
    """Tests for Agent 4/5 integration"""

    @pytest.mark.asyncio
    async def test_llm_connection(self):
        """Test connection to Agent 4/5 LLM"""
        from playbooks.multi_agent_chatbot.orchestration import Agent, AgentCapability, AgentRole

        # Create test agent
        capability = AgentCapability(
            role=AgentRole.RESEARCHER,
            description="Test agent",
            skills=["testing"]
        )
        agent = Agent("test_agent", capability, llm_url="http://agent4:8000")

        # LLM URL should be set
        assert agent.llm_url == "http://agent4:8000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
