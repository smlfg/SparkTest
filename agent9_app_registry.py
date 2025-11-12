"""
Agent 9: Application Layer Registry
Scope: End-user applications and interfaces

This module serves as the central registry for all Agent 9 applications,
providing service discovery and health monitoring capabilities.

Dependencies:
- Agent 4/5 (inference services)
- Agent 8 (multi-modal processing)
"""

import asyncio
import aiohttp
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ApplicationInfo:
    """Application metadata and configuration"""
    name: str
    url: str
    description: str
    playbook: str
    dependencies: List[str]
    health_endpoint: Optional[str] = None


# Primary application registry
APPLICATIONS = {
    "comfy_ui": "http://localhost:8188",
    "rag_ui": "http://localhost:3000",
    "chatbot": "http://localhost:8080",
    "kg_viz": "http://localhost:3001"
}


# Extended application metadata
APPLICATION_METADATA = {
    "comfy_ui": ApplicationInfo(
        name="ComfyUI",
        url=APPLICATIONS["comfy_ui"],
        description="Advanced image generation interface with node-based workflow",
        playbook="comfy-ui",
        dependencies=["agent4", "agent5", "agent8"],
        health_endpoint="/system_stats"
    ),
    "rag_ui": ApplicationInfo(
        name="RAG AI Workbench",
        url=APPLICATIONS["rag_ui"],
        description="Retrieval-Augmented Generation pipeline with vector search",
        playbook="rag-ai-workbench",
        dependencies=["agent4", "agent5"],
        health_endpoint="/health"
    ),
    "chatbot": ApplicationInfo(
        name="Multi-Agent Chatbot",
        url=APPLICATIONS["chatbot"],
        description="Orchestrated multi-agent conversational system",
        playbook="multi-agent-chatbot",
        dependencies=["agent4", "agent5"],
        health_endpoint="/health"
    ),
    "kg_viz": ApplicationInfo(
        name="Knowledge Graph Visualizer",
        url=APPLICATIONS["kg_viz"],
        description="Text to Knowledge Graph pipeline with visualization",
        playbook="txt2kg",
        dependencies=["agent4", "agent5"],
        health_endpoint="/health"
    )
}


# Additional service endpoints (not in main APPLICATIONS dict)
EXTENDED_SERVICES = {
    "vss": {
        "url": "http://localhost:8081",
        "name": "Video Search & Summarization",
        "playbook": "vss",
        "dependencies": ["agent8"]
    }
}


class ApplicationRegistry:
    """
    Central registry for managing and monitoring Agent 9 applications
    """

    def __init__(self):
        self.applications = APPLICATIONS.copy()
        self.metadata = APPLICATION_METADATA.copy()
        self._health_cache: Dict[str, ServiceStatus] = {}

    async def check_health(self, app_name: str, timeout: int = 5) -> ServiceStatus:
        """
        Check health status of an application

        Args:
            app_name: Application identifier
            timeout: Request timeout in seconds

        Returns:
            ServiceStatus indicating application health
        """
        if app_name not in self.metadata:
            logger.warning(f"Application {app_name} not found in registry")
            return ServiceStatus.UNKNOWN

        app_info = self.metadata[app_name]
        if not app_info.health_endpoint:
            return ServiceStatus.UNKNOWN

        health_url = f"{app_info.url}{app_info.health_endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=timeout) as response:
                    if response.status == 200:
                        self._health_cache[app_name] = ServiceStatus.HEALTHY
                        return ServiceStatus.HEALTHY
                    else:
                        self._health_cache[app_name] = ServiceStatus.UNHEALTHY
                        return ServiceStatus.UNHEALTHY
        except Exception as e:
            logger.error(f"Health check failed for {app_name}: {e}")
            self._health_cache[app_name] = ServiceStatus.UNHEALTHY
            return ServiceStatus.UNHEALTHY

    async def check_all_health(self) -> Dict[str, ServiceStatus]:
        """
        Check health status of all registered applications

        Returns:
            Dictionary mapping app names to health status
        """
        tasks = [self.check_health(app_name) for app_name in self.applications.keys()]
        results = await asyncio.gather(*tasks)
        return dict(zip(self.applications.keys(), results))

    def get_app_url(self, app_name: str) -> Optional[str]:
        """Get application URL by name"""
        return self.applications.get(app_name)

    def get_app_info(self, app_name: str) -> Optional[ApplicationInfo]:
        """Get full application metadata"""
        return self.metadata.get(app_name)

    def list_applications(self) -> List[str]:
        """List all registered application names"""
        return list(self.applications.keys())

    def get_by_playbook(self, playbook: str) -> List[ApplicationInfo]:
        """Find all applications using a specific playbook"""
        return [
            info for info in self.metadata.values()
            if info.playbook == playbook
        ]

    def register_application(self, app_name: str, url: str, metadata: ApplicationInfo):
        """Dynamically register a new application"""
        self.applications[app_name] = url
        self.metadata[app_name] = metadata
        logger.info(f"Registered new application: {app_name} at {url}")


# Singleton instance
_registry_instance = None


def get_registry() -> ApplicationRegistry:
    """Get singleton registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ApplicationRegistry()
    return _registry_instance


async def main():
    """Demo: Check health of all applications"""
    registry = get_registry()

    print("Agent 9 Application Registry")
    print("=" * 50)
    print("\nRegistered Applications:")

    for app_name in registry.list_applications():
        app_info = registry.get_app_info(app_name)
        if app_info:
            print(f"\n  {app_info.name}")
            print(f"    URL: {app_info.url}")
            print(f"    Playbook: {app_info.playbook}")
            print(f"    Description: {app_info.description}")
            print(f"    Dependencies: {', '.join(app_info.dependencies)}")

    print("\n" + "=" * 50)
    print("\nHealth Check Results:")

    health_results = await registry.check_all_health()
    for app_name, status in health_results.items():
        status_icon = "✓" if status == ServiceStatus.HEALTHY else "✗"
        print(f"  {status_icon} {app_name}: {status.value}")


if __name__ == "__main__":
    asyncio.run(main())
