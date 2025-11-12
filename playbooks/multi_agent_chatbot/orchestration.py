"""
Multi-Agent Chatbot Orchestration
Orchestrated multi-agent conversational system with specialized agents

Dependencies: Agent 4/5 (inference)
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Specialized agent roles"""
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    CRITIC = "critic"
    EXECUTOR = "executor"


class MessageType(Enum):
    """Message types in multi-agent system"""
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    INTERNAL_COMMUNICATION = "internal"
    SYSTEM_MESSAGE = "system"


@dataclass
class Message:
    """Message in the conversation"""
    id: str
    type: MessageType
    sender: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    parent_id: Optional[str] = None


@dataclass
class AgentCapability:
    """Describes an agent's capabilities"""
    role: AgentRole
    description: str
    skills: List[str]
    model: str = "gpt-4"


@dataclass
class ConversationContext:
    """Maintains conversation state"""
    conversation_id: str
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def add_message(self, message: Message):
        """Add a message to the conversation"""
        self.messages.append(message)

    def get_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get conversation history"""
        if limit:
            return self.messages[-limit:]
        return self.messages

    def get_last_user_message(self) -> Optional[Message]:
        """Get the most recent user message"""
        for msg in reversed(self.messages):
            if msg.type == MessageType.USER_INPUT:
                return msg
        return None


class Agent:
    """
    Base class for specialized agents in the multi-agent system
    """

    def __init__(
        self,
        agent_id: str,
        capability: AgentCapability,
        llm_url: str = "http://localhost:8000"
    ):
        self.agent_id = agent_id
        self.capability = capability
        self.llm_url = llm_url

    async def process(
        self,
        message: str,
        context: ConversationContext,
        **kwargs
    ) -> str:
        """
        Process a message and generate a response

        Args:
            message: Input message
            context: Conversation context
            **kwargs: Additional arguments

        Returns:
            Agent's response
        """
        # Build prompt based on role
        prompt = self._build_prompt(message, context)

        # Call LLM service
        response = await self._call_llm(prompt)

        return response

    def _build_prompt(self, message: str, context: ConversationContext) -> str:
        """Build role-specific prompt"""
        role_prompts = {
            AgentRole.COORDINATOR: f"You are a coordinator agent. Analyze the request and determine the best approach.\n\nRequest: {message}",
            AgentRole.RESEARCHER: f"You are a research agent. Find and synthesize relevant information.\n\nQuery: {message}",
            AgentRole.ANALYST: f"You are an analyst agent. Analyze the data and provide insights.\n\nData: {message}",
            AgentRole.WRITER: f"You are a writer agent. Create well-structured content.\n\nTopic: {message}",
            AgentRole.CRITIC: f"You are a critic agent. Review and provide constructive feedback.\n\nContent: {message}",
            AgentRole.EXECUTOR: f"You are an executor agent. Execute tasks and report results.\n\nTask: {message}"
        }

        base_prompt = role_prompts.get(
            self.capability.role,
            f"You are a helpful assistant.\n\nQuery: {message}"
        )

        # Add conversation history if available
        history = context.get_history(limit=5)
        if len(history) > 1:
            history_str = "\n".join([
                f"{msg.sender}: {msg.content}"
                for msg in history[-5:-1]  # Exclude current message
            ])
            base_prompt = f"Conversation history:\n{history_str}\n\n{base_prompt}"

        return base_prompt

    async def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Call LLM inference service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_url}/generate",
                    json={
                        "prompt": prompt,
                        "model": self.capability.model,
                        "max_tokens": max_tokens,
                        "temperature": 0.7
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("text", "Error: No response")
                    else:
                        logger.error(f"LLM call failed: {response.status}")
                        return f"[{self.capability.role.value} agent]: Processing..."
        except Exception as e:
            logger.error(f"LLM service error: {e}")
            return f"[{self.capability.role.value} agent]: Unable to process request"


class CoordinatorAgent(Agent):
    """
    Coordinator agent that orchestrates other agents
    """

    def __init__(self, agent_id: str = "coordinator", llm_url: str = "http://localhost:8000"):
        capability = AgentCapability(
            role=AgentRole.COORDINATOR,
            description="Orchestrates and coordinates other agents",
            skills=["task_decomposition", "agent_selection", "result_synthesis"]
        )
        super().__init__(agent_id, capability, llm_url)

    async def coordinate(
        self,
        user_input: str,
        available_agents: Dict[str, Agent],
        context: ConversationContext
    ) -> str:
        """
        Coordinate multiple agents to handle complex queries

        Args:
            user_input: User's query
            available_agents: Dictionary of available agents
            context: Conversation context

        Returns:
            Coordinated response
        """
        # Step 1: Analyze the request
        analysis_prompt = f"""Analyze this user request and determine which agents should handle it.
Available agents: {', '.join([f'{k} ({v.capability.role.value})' for k, v in available_agents.items()])}

User request: {user_input}

Provide a brief analysis and list the agents to involve."""

        analysis = await self._call_llm(analysis_prompt)

        # Step 2: Route to appropriate agents (simplified)
        # In a real system, this would parse the analysis and route accordingly
        responses = []

        # For demo, we'll route to researcher and analyst for complex questions
        if any(word in user_input.lower() for word in ["analyze", "research", "explain", "how", "why"]):
            if "researcher" in available_agents:
                researcher_response = await available_agents["researcher"].process(
                    user_input, context
                )
                responses.append(f"Researcher: {researcher_response}")

            if "analyst" in available_agents:
                analyst_response = await available_agents["analyst"].process(
                    user_input, context
                )
                responses.append(f"Analyst: {analyst_response}")

        # Step 3: Synthesize responses
        if responses:
            synthesis_prompt = f"""Synthesize these agent responses into a coherent answer:

{chr(10).join(responses)}

Provide a unified, comprehensive response to: {user_input}"""

            final_response = await self._call_llm(synthesis_prompt, max_tokens=800)
            return final_response
        else:
            # Single agent response
            return await self.process(user_input, context)


class MultiAgentChatbot:
    """
    Multi-agent chatbot orchestration system
    """

    def __init__(
        self,
        llm_url: str = "http://localhost:8000",
        port: int = 8080
    ):
        self.llm_url = llm_url
        self.port = port
        self.agents: Dict[str, Agent] = {}
        self.coordinator: Optional[CoordinatorAgent] = None
        self.conversations: Dict[str, ConversationContext] = {}

        # Initialize default agents
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize the agent team"""
        # Coordinator
        self.coordinator = CoordinatorAgent(llm_url=self.llm_url)

        # Specialized agents
        self.agents["researcher"] = Agent(
            "researcher",
            AgentCapability(
                role=AgentRole.RESEARCHER,
                description="Conducts research and gathers information",
                skills=["information_retrieval", "synthesis", "fact_checking"]
            ),
            self.llm_url
        )

        self.agents["analyst"] = Agent(
            "analyst",
            AgentCapability(
                role=AgentRole.ANALYST,
                description="Analyzes data and provides insights",
                skills=["data_analysis", "pattern_recognition", "interpretation"]
            ),
            self.llm_url
        )

        self.agents["writer"] = Agent(
            "writer",
            AgentCapability(
                role=AgentRole.WRITER,
                description="Creates well-written content",
                skills=["content_creation", "editing", "formatting"]
            ),
            self.llm_url
        )

        self.agents["critic"] = Agent(
            "critic",
            AgentCapability(
                role=AgentRole.CRITIC,
                description="Reviews and provides constructive feedback",
                skills=["critical_analysis", "quality_assessment", "improvement_suggestions"]
            ),
            self.llm_url
        )

        logger.info(f"Initialized {len(self.agents)} specialized agents")

    def create_conversation(self, conversation_id: str) -> ConversationContext:
        """Create a new conversation context"""
        context = ConversationContext(conversation_id=conversation_id)
        self.conversations[conversation_id] = context
        return context

    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get existing conversation context"""
        return self.conversations.get(conversation_id)

    async def chat(
        self,
        user_input: str,
        conversation_id: str,
        use_coordination: bool = True
    ) -> Dict[str, Any]:
        """
        Process user input and generate response

        Args:
            user_input: User's message
            conversation_id: Conversation identifier
            use_coordination: Whether to use multi-agent coordination

        Returns:
            Response dictionary with answer and metadata
        """
        # Get or create conversation context
        context = self.get_conversation(conversation_id)
        if context is None:
            context = self.create_conversation(conversation_id)

        # Add user message to context
        user_message = Message(
            id=f"{conversation_id}_{len(context.messages)}",
            type=MessageType.USER_INPUT,
            sender="user",
            content=user_input
        )
        context.add_message(user_message)

        # Generate response
        start_time = datetime.now()

        if use_coordination and self.coordinator:
            response_text = await self.coordinator.coordinate(
                user_input,
                self.agents,
                context
            )
        else:
            # Simple single-agent response
            default_agent = self.agents.get("researcher") or list(self.agents.values())[0]
            response_text = await default_agent.process(user_input, context)

        # Add assistant message to context
        assistant_message = Message(
            id=f"{conversation_id}_{len(context.messages)}",
            type=MessageType.AGENT_RESPONSE,
            sender="assistant",
            content=response_text,
            parent_id=user_message.id
        )
        context.add_message(assistant_message)

        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            "conversation_id": conversation_id,
            "response": response_text,
            "metadata": {
                "processing_time": processing_time,
                "num_agents": len(self.agents),
                "coordination_used": use_coordination,
                "message_count": len(context.messages)
            }
        }

    def get_agent_info(self) -> List[Dict[str, Any]]:
        """Get information about all agents"""
        agents_info = [
            {
                "id": agent_id,
                "role": agent.capability.role.value,
                "description": agent.capability.description,
                "skills": agent.capability.skills
            }
            for agent_id, agent in self.agents.items()
        ]

        if self.coordinator:
            agents_info.insert(0, {
                "id": "coordinator",
                "role": "coordinator",
                "description": "Orchestrates multi-agent collaboration",
                "skills": ["orchestration", "task_decomposition", "synthesis"]
            })

        return agents_info


async def main():
    """Demo multi-agent chatbot"""
    print("Multi-Agent Chatbot Orchestration")
    print("=" * 50)

    # Initialize chatbot
    chatbot = MultiAgentChatbot(llm_url="http://localhost:8000", port=8080)

    # Display agent information
    print("\nAvailable Agents:")
    for agent_info in chatbot.get_agent_info():
        print(f"\n  {agent_info['id'].upper()} ({agent_info['role']})")
        print(f"    Description: {agent_info['description']}")
        print(f"    Skills: {', '.join(agent_info['skills'])}")

    # Example conversations
    conversation_id = "demo_conversation_001"

    example_queries = [
        "Explain how Apache Spark's distributed computing works",
        "Analyze the benefits of using Spark over MapReduce",
        "Write a summary of Spark's core components"
    ]

    print("\n" + "=" * 50)
    print("Example Conversations:")
    print("=" * 50)

    for query in example_queries:
        print(f"\nUser: {query}")
        print("-" * 50)

        response = await chatbot.chat(
            user_input=query,
            conversation_id=conversation_id,
            use_coordination=True
        )

        print(f"Assistant: {response['response']}")
        print(f"\nMetadata:")
        print(f"  Processing time: {response['metadata']['processing_time']:.2f}s")
        print(f"  Agents involved: {response['metadata']['num_agents']}")
        print(f"  Coordination: {response['metadata']['coordination_used']}")

    # Conversation statistics
    context = chatbot.get_conversation(conversation_id)
    if context:
        print("\n" + "=" * 50)
        print(f"Conversation Statistics:")
        print(f"  Total messages: {len(context.messages)}")
        print(f"  Duration: {(datetime.now() - context.created_at).total_seconds():.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
