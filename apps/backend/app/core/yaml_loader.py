import yaml
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from ..types.agent import Agent

class AgentLoader:
    def __init__(self, agents_file: Path):
        self.agents_file = agents_file
        self.agents: List[Agent] = []
        self._load_agents()

    def _load_agents(self):
        """Load agents from YAML file"""
        try:
            with open(self.agents_file, 'r') as f:
                data = yaml.safe_load(f)
                
                # Convert YAML data to Pydantic models
                self.agents = [
                    Agent(
                        id=agent_data['id'],
                        name=agent_data['name'],
                        description=agent_data['description'],
                        capabilities=[
                            AgentCapability(
                                name=cap['name'],
                                description=cap.get('description')
                            )
                            for cap in agent_data.get('capabilities', [])
                        ],
                        model=agent_data['model'],
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    for agent_data in data.get('agents', [])
                ]
        except Exception as e:
            print(f"Error loading agents: {e}")
            self.agents = []

    def get_agents(self) -> List[Agent]:
        """Get all agents"""
        return self.agents

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get a specific agent by ID"""
        return next((agent for agent in self.agents if agent.id == agent_id), None)
