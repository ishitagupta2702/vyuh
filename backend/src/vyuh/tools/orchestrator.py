import uuid
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from crewai import Agent, Task, Crew
from langchain_community.chat_models import ChatLiteLLM

# Add sandbox path to import sandbox tools
project_root = Path(__file__).parent.parent.parent
sandbox_path = project_root / "sandbox"
sys.path.insert(0, str(sandbox_path))

from .graph_utils import list_to_graph
from .loaders import load_agents, load_tasks


def launch_crew_from_linear_list(crew: List[str], topic: str, session_id: str = None) -> dict:
    """
    Launch a CrewAI workflow from a linear list of agent IDs.
    
    Args:
        crew: List of agent IDs in execution order
        topic: The topic for the crew to work on
        
    Returns:
        Dictionary containing session_id and the actual crew execution result
        
    Raises:
        ValueError: If any agent is not found in configuration
        ValueError: If any task is not found for an agent
    """
    print(f"[ORCHESTRATOR] Starting crew launch: crew={crew}, topic={topic}")
    
    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())
    print(f"[ORCHESTRATOR] Using session_id: {session_id}")
    
    # Step 1: Convert list to graph
    print("[ORCHESTRATOR] Converting list to graph...")
    graph = list_to_graph(crew)
    print(f"[ORCHESTRATOR] Graph: {graph}")
    
    # Step 2: Load agents and tasks
    print("[ORCHESTRATOR] Loading agents and tasks...")
    agents_config = load_agents()
    tasks_config = load_tasks()
    print(f"[ORCHESTRATOR] Loaded {len(agents_config)} agents, {len(tasks_config)} tasks")
    
    # Step 3: Validate all agents exist
    print("[ORCHESTRATOR] Validating agents...")
    for agent_id in crew:
        if agent_id not in agents_config:
            raise ValueError(f"Agent '{agent_id}' not found in configuration")
    
    # Step 4: Create CrewAI Agents and Tasks
    print("[ORCHESTRATOR] Creating CrewAI Agents and Tasks...")
    crew_agents = {}
    crew_tasks = {}
    
    for agent_id in crew:
        print(f"[ORCHESTRATOR] Processing agent: {agent_id}")
        
        # Create Agent
        agent_config = agents_config[agent_id]
        crew_agents[agent_id] = Agent(
            role=agent_config.get("role", "").strip(),
            goal=agent_config.get("goal", "").strip(),
            backstory=agent_config.get("backstory", "").strip(),
            llm=ChatLiteLLM(model="gpt-3.5-turbo"),
            verbose=True
        )
        
        # Add sandbox tools based on agent type
        try:
            from crewai_tools import create_file_tool, create_command_tool, create_pdf_tool
            
            # Create a sandbox manager for this agent
            from sandbox import SandboxManager
            sandbox_manager = SandboxManager()
            
            # Add tools based on agent role
            if "researcher" in agent_id.lower():
                crew_agents[agent_id].tools = [
                    create_file_tool(sandbox_manager),
                    create_command_tool(sandbox_manager)
                ]
            elif "writer" in agent_id.lower():
                crew_agents[agent_id].tools = [
                    create_file_tool(sandbox_manager),
                    create_pdf_tool(sandbox_manager)
                ]
            else:
                # Default tools for other agents
                crew_agents[agent_id].tools = [create_file_tool(sandbox_manager)]
                
            print(f"[ORCHESTRATOR] Added sandbox tools to agent: {agent_id}")
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Warning: Could not add sandbox tools to {agent_id}: {e}")
        
        print(f"[ORCHESTRATOR] Created agent: {agent_id}")
        
        # Find corresponding task
        task_id = None
        for tid, task_config in tasks_config.items():
            if task_config.get("agent") == agent_id:
                task_id = tid
                break
        
        if not task_id:
            raise ValueError(f"No task found for agent: {agent_id}")
        
        # Create Task
        task_config = tasks_config[task_id]
        crew_tasks[agent_id] = Task(
            description=task_config.get("description", "").strip(),
            expected_output=task_config.get("expected_output", "").strip(),
            agent=crew_agents[agent_id],
            context=[]
        )
        print(f"[ORCHESTRATOR] Created task: {task_id} for agent: {agent_id}")
    
    # Step 5: Wire tasks based on graph dependencies
    print("[ORCHESTRATOR] Wiring tasks based on graph...")
    for agent_id, successors in graph.items():
        if agent_id in crew_tasks and successors:
            # Add dependencies for each successor
            for successor_id in successors:
                if successor_id in crew_tasks:
                    crew_tasks[successor_id].context.append(crew_tasks[agent_id])
                    print(f"[ORCHESTRATOR] Wired {agent_id} -> {successor_id}")
    
    # Step 6: Create Crew
    print("[ORCHESTRATOR] Creating crew...")
    crew_instance = Crew(
        agents=list(crew_agents.values()),
        tasks=list(crew_tasks.values()),
        verbose=True
    )
    print(f"[ORCHESTRATOR] Created crew with {len(crew_agents)} agents and {len(crew_tasks)} tasks")
    
    # Step 7: Run the crew
    print("[ORCHESTRATOR] Starting crew execution...")
    try:
        result = crew_instance.kickoff(inputs={"topic": topic})
        print(f"[ORCHESTRATOR] Session {session_id}: Crew execution completed successfully")
        print(f"[ORCHESTRATOR] Session {session_id}: Result: {result}")
        
        # Return the actual result data directly
        return {
            "session_id": session_id,
            "result": str(result),
            "topic": topic,
            "crew": crew
        }
    except Exception as e:
        print(f"[ORCHESTRATOR] Session {session_id}: Crew execution failed - {str(e)}")
        raise e


def launch_crew_from_linear_list_with_queue(crew: List[str], topic: str, session_id: str = None, queue_job: bool = False) -> dict:
    """
    Launch a CrewAI workflow from a linear list of agent IDs with option to queue.
    
    Args:
        crew: List of agent IDs in execution order
        topic: The topic for the crew to work on
        session_id: Optional session ID
        queue_job: If True, queue the job instead of running synchronously
        
    Returns:
        Dictionary containing session_id and result or job_id
    """
    if queue_job:
        # Queue the job for background execution
        try:
            from worker import queue_crew_workflow
            
            # Create crew configuration
            crew_config = {
                "agents": [
                    {
                        "role": "researcher" if "researcher" in agent else "writer" if "writer" in agent else "agent",
                        "goal": f"Process {topic}",
                        "backstory": f"Specialized agent for {agent} operations",
                        "verbose": True,
                        "allow_delegation": False
                    }
                    for agent in crew
                ],
                "tasks": [
                    {
                        "description": f"Execute {agent} task for {topic}",
                        "agent_index": i,
                        "expected_output": f"Results from {agent}",
                        "context": []
                    }
                    for i, agent in enumerate(crew)
                ],
                "verbose": True
            }
            
            job_id = queue_crew_workflow(crew_config, topic)
            
            return {
                "session_id": session_id,
                "job_id": job_id,
                "status": "queued",
                "topic": topic,
                "crew": crew
            }
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Failed to queue job: {e}")
            # Fall back to synchronous execution
            pass
    
    # Fall back to synchronous execution
    return launch_crew_from_linear_list(crew, topic, session_id)


if __name__ == "__main__":
    # Test the orchestrator
    try:
        print("Testing launch_crew_from_linear_list...")
        crew_list = ["researcher", "writer"]
        topic = "AI research"
        
        result = launch_crew_from_linear_list(crew_list, topic)
        print(f"✅ Crew launched successfully with session_id: {result['session_id']}")
        print(f"📝 Result: {result['result'][:100]}...")  # Show first 100 chars
        
    except Exception as e:
        print(f"❌ Error: {e}")