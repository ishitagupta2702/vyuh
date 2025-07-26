from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid
from ..types.agent import Workflow, WorkflowStep
from ..core.yaml_loader import AgentLoader

class WorkflowManager:
    def __init__(self, agents_file: Path):
        self.agent_loader = AgentLoader(agents_file)
        self.workflows: Dict[str, Workflow] = {}
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

    def _save_workflow(self, workflow: Workflow):
        """Save workflow to disk"""
        data_dir = Path("data")
        workflow_file = data_dir / f"workflow_{workflow.id}.json"
        with open(workflow_file, 'w') as f:
            json.dump(
                {
                    "id": workflow.id,
                    "steps": [step.dict() for step in workflow.steps],
                    "status": workflow.status,
                    "created_at": workflow.created_at.isoformat(),
                    "updated_at": workflow.updated_at.isoformat()
                },
                f,
                indent=2
            )

    def _load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Load workflow from disk"""
        data_dir = Path("data")
        workflow_file = data_dir / f"workflow_{workflow_id}.json"
        if not workflow_file.exists():
            return None

        with open(workflow_file, 'r') as f:
            data = json.load(f)
            return Workflow(
                id=data["id"],
                steps=[WorkflowStep(**step) for step in data["steps"]],
                status=data["status"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )

    def create_workflow(self, steps: List[WorkflowStep]) -> str:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            steps=steps,
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.workflows[workflow_id] = workflow
        self._save_workflow(workflow)
        return workflow_id

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        if workflow_id in self.workflows:
            return self.workflows[workflow_id]
        return self._load_workflow(workflow_id)

    def run_workflow(self, workflow_id: str) -> str:
        """Execute a workflow"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Mock implementation - in production this would:
        # 1. Validate agent IDs
        # 2. Execute each step in sequence
        # 3. Store results
        
        workflow.status = "running"
        workflow.updated_at = datetime.now()
        
        # Mock execution
        for step in workflow.steps:
            agent = self.agent_loader.get_agent(step.agent_id)
            if not agent:
                raise ValueError(f"Agent {step.agent_id} not found")
            
            # Mock step execution
            step.output_data = {
                "status": "completed",
                "agent": agent.name,
                "timestamp": datetime.now().isoformat()
            }

        workflow.status = "completed"
        workflow.updated_at = datetime.now()
        
        self.workflows[workflow_id] = workflow
        self._save_workflow(workflow)
        
        return f"Workflow {workflow_id} executed successfully"

# Initialize workflow manager
workflow_manager = WorkflowManager(Path("../../packages/shared/agents.yaml"))
