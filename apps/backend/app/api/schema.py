import strawberry
from strawberry.fastapi import GraphQLRouter
from datetime import datetime
from typing import List, Optional
from packages.shared.types.agent import Agent, Workflow, WorkflowInput, WorkflowStep
from ..core.yaml_loader import AgentLoader
from ..services.workflow.manager import workflow_manager
from pathlib import Path

@strawberry.type
class Query:
    @strawberry.field
    def list_agents(self) -> List[Agent]:
        """List all available agents"""
        return agent_loader.get_agents()

    @strawberry.field
    def get_agent(self, id: str) -> Optional[Agent]:
        """Get details of a specific agent"""
        return agent_loader.get_agent(id)

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_workflow(self, input: WorkflowInput) -> str:
        """Create a new workflow"""
        return workflow_manager.create_workflow(input.steps)

    @strawberry.mutation
    def run_workflow(self, workflow_id: str) -> str:
        """Execute a workflow"""
        return workflow_manager.run_workflow(workflow_id)

# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Create GraphQL router
graphql_app = GraphQLRouter(schema)
