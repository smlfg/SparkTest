#!/usr/bin/env python3
"""
Agent 1 Infrastructure Foundation - Output Interface Module
Provides cluster configuration and connection details for downstream agents
"""

import json
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional


# Default cluster configuration
CLUSTER_CONFIG = {
    "nodes": ["spark-001.local", "spark-002.local"],
    "ssh_keys": "/home/user/.ssh/dgx_key",
    "tailscale_ip": "100.x.x.x"
}


class Agent1Output:
    """Interface for Agent 1 Infrastructure Foundation outputs"""

    def __init__(self, config_dir: str = None):
        self.base_dir = Path(__file__).parent
        self.config_dir = Path(config_dir) if config_dir else self.base_dir / "config"
        self.config_dir.mkdir(exist_ok=True)

    def load_cluster_config(self, config_file: str = "cluster.yaml") -> Dict:
        """Load cluster configuration from YAML file"""
        config_path = self.config_dir / config_file

        if not config_path.exists():
            return CLUSTER_CONFIG.copy()

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return self._parse_cluster_config(config)

    def _parse_cluster_config(self, config: Dict) -> Dict:
        """Parse and normalize cluster configuration"""
        nodes = []

        # Extract node information
        if "nodes" in config:
            for node in config["nodes"]:
                if isinstance(node, dict):
                    nodes.append(node.get("hostname") or node.get("ip"))
                else:
                    nodes.append(str(node))

        return {
            "cluster_name": config.get("cluster_name", "spark-cluster"),
            "nodes": nodes,
            "ssh_keys": config.get("ssh_key_path", "/home/user/.ssh/dgx_key"),
            "tailscale_ip": self.get_tailscale_ip(),
            "primary_node": nodes[0] if nodes else None,
            "node_count": len(nodes)
        }

    def get_tailscale_ip(self) -> Optional[str]:
        """Get Tailscale IP from configuration"""
        tailscale_env = self.config_dir / "tailscale.env"

        if not tailscale_env.exists():
            return None

        try:
            with open(tailscale_env, 'r') as f:
                for line in f:
                    if line.startswith("TAILSCALE_IP="):
                        return line.strip().split('=')[1]
        except Exception:
            pass

        return None

    def get_ssh_config(self) -> Dict:
        """Get SSH configuration details"""
        config = self.load_cluster_config()

        return {
            "key_path": config["ssh_keys"],
            "key_type": "ed25519",
            "user": os.getenv("USER", "user"),
            "port": 22,
            "options": {
                "StrictHostKeyChecking": "accept-new",
                "ServerAliveInterval": 60,
                "ServerAliveCountMax": 3
            }
        }

    def get_network_config(self) -> Dict:
        """Get network configuration details"""
        config = self.load_cluster_config()

        return {
            "cluster_name": config["cluster_name"],
            "nodes": config["nodes"],
            "tailscale_enabled": config["tailscale_ip"] is not None,
            "tailscale_ip": config["tailscale_ip"],
            "primary_node": config["primary_node"]
        }

    def get_nccl_config(self) -> Dict:
        """Get NCCL configuration for multi-GPU communication"""
        nccl_conf = self.config_dir / ".." / "config" / "nccl.env"

        config = {
            "enabled": False,
            "socket_ifname": None,
            "ib_disable": "1",
            "debug_level": "INFO"
        }

        if nccl_conf.exists():
            try:
                with open(nccl_conf, 'r') as f:
                    for line in f:
                        if "NCCL_SOCKET_IFNAME=" in line:
                            config["socket_ifname"] = line.strip().split('=')[1]
                        elif "NCCL_IB_DISABLE=" in line:
                            config["ib_disable"] = line.strip().split('=')[1]
                        elif "NCCL_DEBUG=" in line:
                            config["debug_level"] = line.strip().split('=')[1]

                config["enabled"] = True
            except Exception:
                pass

        return config

    def get_cluster_endpoints(self) -> List[Dict]:
        """Get list of cluster endpoints with connection details"""
        config = self.load_cluster_config()
        ssh_config = self.get_ssh_config()

        endpoints = []

        for node in config["nodes"]:
            endpoint = {
                "hostname": node,
                "ssh_user": ssh_config["user"],
                "ssh_key": ssh_config["key_path"],
                "ssh_port": ssh_config["port"],
                "connection_string": f"ssh -i {ssh_config['key_path']} {ssh_config['user']}@{node}"
            }

            endpoints.append(endpoint)

        return endpoints

    def export_config(self, output_file: str = None) -> str:
        """Export complete cluster configuration to JSON"""
        config = {
            "cluster": self.load_cluster_config(),
            "ssh": self.get_ssh_config(),
            "network": self.get_network_config(),
            "nccl": self.get_nccl_config(),
            "endpoints": self.get_cluster_endpoints()
        }

        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
            return str(output_path)
        else:
            return json.dumps(config, indent=2)

    def get_connection_command(self, node: str = None) -> str:
        """Get SSH connection command for a node"""
        config = self.load_cluster_config()
        ssh_config = self.get_ssh_config()

        target_node = node or config["primary_node"]

        if not target_node:
            return "# No nodes configured"

        return f"ssh -i {ssh_config['key_path']} {ssh_config['user']}@{target_node}"

    def validate_setup(self) -> Dict:
        """Validate that infrastructure setup is complete"""
        validation = {
            "config_exists": (self.config_dir / "cluster.yaml").exists(),
            "ssh_key_exists": Path(self.get_ssh_config()["key_path"]).exists(),
            "inventory_exists": (self.config_dir / "inventory.ini").exists(),
            "tailscale_configured": self.get_tailscale_ip() is not None,
            "nccl_configured": self.get_nccl_config()["enabled"],
            "student_users_configured": (self.config_dir / "students.conf").exists()
        }

        validation["ready"] = validation["config_exists"] and validation["ssh_key_exists"]

        return validation

    def get_student_config(self) -> Dict:
        """Get student user management configuration"""
        students_conf = self.config_dir / "students.conf"

        config = {
            "enabled": students_conf.exists(),
            "workspace_base": "/workspace",
            "quota_soft": "50G",
            "quota_hard": "55G",
            "students": []
        }

        if students_conf.exists():
            try:
                # Parse bash config file
                with open(students_conf, 'r') as f:
                    content = f.read()

                # Extract students array
                import re
                students_match = re.search(r'STUDENTS=\((.*?)\)', content, re.DOTALL)
                if students_match:
                    students_str = students_match.group(1)
                    config["students"] = [s.strip().strip('"').strip("'")
                                        for s in students_str.split()
                                        if s.strip()]

                # Extract other config values
                for line in content.split('\n'):
                    if line.startswith('WORKSPACE_BASE='):
                        config["workspace_base"] = line.split('=')[1].strip('"').strip("'")
                    elif line.startswith('QUOTA_SOFT='):
                        config["quota_soft"] = line.split('=')[1].strip('"').strip("'")
                    elif line.startswith('QUOTA_HARD='):
                        config["quota_hard"] = line.split('=')[1].strip('"').strip("'")

            except Exception as e:
                config["error"] = str(e)

        return config

    def list_student_users(self) -> List[Dict]:
        """List all student users on the cluster"""
        from pathlib import Path

        student_config = self.get_student_config()
        workspace_base = Path(student_config["workspace_base"])

        if not workspace_base.exists():
            return []

        students = []
        for workspace in workspace_base.iterdir():
            if workspace.is_dir():
                username = workspace.name
                students.append({
                    "username": username,
                    "workspace": str(workspace),
                    "exists": workspace.exists()
                })

        return students


def get_cluster_config() -> Dict:
    """
    Main interface function for downstream agents
    Returns the complete cluster configuration
    """
    agent = Agent1Output()
    return agent.load_cluster_config()


def get_connection_info() -> Dict:
    """
    Get connection information for downstream agents
    Returns SSH and network configuration
    """
    agent = Agent1Output()
    return {
        "ssh": agent.get_ssh_config(),
        "network": agent.get_network_config(),
        "nccl": agent.get_nccl_config()
    }


def get_student_info() -> Dict:
    """
    Get student user management information
    Returns student configuration and list
    """
    agent = Agent1Output()
    return {
        "config": agent.get_student_config(),
        "users": agent.list_student_users()
    }


# Example usage
if __name__ == "__main__":
    import sys

    agent = Agent1Output()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "config":
            print(json.dumps(agent.load_cluster_config(), indent=2))
        elif command == "ssh":
            print(json.dumps(agent.get_ssh_config(), indent=2))
        elif command == "network":
            print(json.dumps(agent.get_network_config(), indent=2))
        elif command == "nccl":
            print(json.dumps(agent.get_nccl_config(), indent=2))
        elif command == "endpoints":
            print(json.dumps(agent.get_cluster_endpoints(), indent=2))
        elif command == "validate":
            validation = agent.validate_setup()
            print(json.dumps(validation, indent=2))
            sys.exit(0 if validation["ready"] else 1)
        elif command == "connect":
            node = sys.argv[2] if len(sys.argv) > 2 else None
            print(agent.get_connection_command(node))
        elif command == "export":
            output = sys.argv[2] if len(sys.argv) > 2 else "cluster_config.json"
            path = agent.export_config(output)
            print(f"Configuration exported to: {path}")
        elif command == "students":
            student_info = get_student_info()
            print(json.dumps(student_info, indent=2))
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        # Default: print CLUSTER_CONFIG
        print(f"# Agent 1 Infrastructure Foundation - Output Interface\n")
        config = agent.load_cluster_config()
        print(f"CLUSTER_CONFIG = {json.dumps(config, indent=4)}")
