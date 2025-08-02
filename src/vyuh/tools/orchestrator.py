import uuid
import os
from pathlib import Path
from typing import List, Dict, Any
from crewai import Agent, Task, Crew
from langchain_community.chat_models import ChatLiteLLM

from .graph_utils import list_to_graph
from .loaders import load_agents, load_tasks


def launch_crew_from_linear_list(crew: List[str], topic: str, session_id: str = None) -> str:
    """
    Launch a CrewAI workflow from a linear list of agent IDs.
    
    Args:
        crew: List of agent IDs in execution order
        topic: The topic for the crew to work on
        
    Returns:
        Session ID for the crew execution
        
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
        
        # Step 8: Save result to file
        print(f"[ORCHESTRATOR] Session {session_id}: Saving result to file...")
        runs_dir = Path("runs")
        runs_dir.mkdir(exist_ok=True)
        
        result_file = runs_dir / f"{session_id}.txt"
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Topic: {topic}\n")
            f.write(f"Crew: {crew}\n")
            f.write(f"Timestamp: {uuid.uuid4()}\n")
            f.write("\n" + "="*50 + "\n")
            f.write("FINAL OUTPUT:\n")
            f.write("="*50 + "\n")
            f.write(str(result))
            f.write("\n")
        
        print(f"[ORCHESTRATOR] Session {session_id}: Result saved to {result_file}")
        return session_id
    except Exception as e:
        print(f"[ORCHESTRATOR] Session {session_id}: Crew execution failed - {str(e)}")
        raise e


if __name__ == "__main__":
    # Test the orchestrator
    try:
        print("Testing launch_crew_from_linear_list...")
        crew_list = ["researcher", "writer"]
        topic = "AI research"
        
        session_id = launch_crew_from_linear_list(crew_list, topic)
        print(f"✅ Crew launched successfully with session_id: {session_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")