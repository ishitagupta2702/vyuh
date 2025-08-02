import yaml
import uuid
from pathlib import Path
from typing import List, Dict, Any
from crewai import Agent, Crew, Task
from langchain_community.chat_models import ChatLiteLLM
import os

def convert_linear_to_adjacency(crew_list: List[str]) -> Dict[str, List[str]]:
    """
    Convert a linear list of agent IDs to a directed acyclic graph (adjacency list).
    
    Args:
        crew_list: List of agent IDs in execution order
        
    Returns:
        Adjacency list where each agent points to the next agent(s) in the chain
    """
    if not crew_list:
        return {}
    
    adjacency = {}
    
    for i, agent_id in enumerate(crew_list):
        if i == len(crew_list) - 1:
            # Last agent has no successors
            adjacency[agent_id] = []
        else:
            # Agent points to the next agent in the list
            adjacency[agent_id] = [crew_list[i + 1]]
    
    return adjacency

def load_config_files() -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load agents and tasks configuration from YAML files.
    
    Returns:
        Tuple of (agents_config, tasks_config)
    """
    # Get the project root and construct paths
    project_root = Path(__file__).parent.parent.parent
    agents_file = project_root / "src" / "vyuh" / "config" / "agents.yaml"
    tasks_file = project_root / "src" / "vyuh" / "config" / "tasks.yaml"
    
    if not agents_file.exists():
        raise FileNotFoundError(f"Agents configuration file not found at {agents_file}")
    
    if not tasks_file.exists():
        raise FileNotFoundError(f"Tasks configuration file not found at {tasks_file}")
    
    with open(agents_file, 'r', encoding='utf-8') as file:
        agents_config = yaml.safe_load(file)
    
    with open(tasks_file, 'r', encoding='utf-8') as file:
        tasks_config = yaml.safe_load(file)
    
    return agents_config, tasks_config

def create_agent(agent_id: str, agent_config: Dict[str, Any]) -> Agent:
    """
    Create a CrewAI Agent from configuration.
    
    Args:
        agent_id: The agent identifier
        agent_config: Agent configuration from YAML
        
    Returns:
        CrewAI Agent object
    """
    return Agent(
        role=agent_config.get("role", "").strip(),
        goal=agent_config.get("goal", "").strip(),
        backstory=agent_config.get("backstory", "").strip(),
        llm=ChatLiteLLM(model="gpt-3.5-turbo"),
        verbose=True
    )

def create_task(task_id: str, task_config: Dict[str, Any], agent: Agent) -> Task:
    """
    Create a CrewAI Task from configuration.
    
    Args:
        task_id: The task identifier
        task_config: Task configuration from YAML
        agent: The agent assigned to this task
        
    Returns:
        CrewAI Task object
    """
    return Task(
        description=task_config.get("description", "").strip(),
        expected_output=task_config.get("expected_output", "").strip(),
        agent=agent
    )

def find_task_for_agent(agent_id: str, tasks_config: Dict[str, Any]) -> str:
    """
    Find the task that corresponds to a given agent.
    
    Args:
        agent_id: The agent identifier
        tasks_config: Tasks configuration from YAML
        
    Returns:
        Task ID that corresponds to the agent
    """
    for task_id, task_config in tasks_config.items():
        if task_config.get("agent") == agent_id:
            return task_id
    raise ValueError(f"No task found for agent: {agent_id}")

def launch_crew_from_linear_list(crew_list: List[str], topic: str) -> str:
    """
    Launch a CrewAI workflow from a linear list of agent IDs.
    
    Args:
        crew_list: List of agent IDs in execution order
        topic: The topic for the crew to work on
        
    Returns:
        Session ID for the crew execution
    """
    print(f"[ORCHESTRATOR] Starting crew launch: crew={crew_list}, topic={topic}")
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    print(f"[ORCHESTRATOR] Generated session_id: {session_id}")
    
    # Load configurations
    print("[ORCHESTRATOR] Loading config files...")
    agents_config, tasks_config = load_config_files()
    print(f"[ORCHESTRATOR] Loaded {len(agents_config)} agents, {len(tasks_config)} tasks")
    
    # Convert linear list to adjacency list
    print("[ORCHESTRATOR] Converting to adjacency list...")
    adjacency = convert_linear_to_adjacency(crew_list)
    print(f"[ORCHESTRATOR] Adjacency list: {adjacency}")
    
    # Create agents and tasks
    print("[ORCHESTRATOR] Creating agents and tasks...")
    agents = {}
    tasks = {}
    
    for agent_id in crew_list:
        print(f"[ORCHESTRATOR] Processing agent: {agent_id}")
        if agent_id not in agents_config:
            raise ValueError(f"Agent '{agent_id}' not found in configuration")
        
        # Create agent
        agent_config = agents_config[agent_id]
        agents[agent_id] = create_agent(agent_id, agent_config)
        print(f"[ORCHESTRATOR] Created agent: {agent_id}")
        
        # Find and create corresponding task
        task_id = find_task_for_agent(agent_id, tasks_config)
        task_config = tasks_config[task_id]
        tasks[agent_id] = create_task(task_id, task_config, agents[agent_id])
        print(f"[ORCHESTRATOR] Created task: {task_id} for agent: {agent_id}")
    
    # Wire tasks based on adjacency list
    print("[ORCHESTRATOR] Wiring tasks...")
    for agent_id, successors in adjacency.items():
        if agent_id in tasks and successors:
            # Add dependencies for each successor
            for successor_id in successors:
                if successor_id in tasks:
                    tasks[successor_id].context.append(tasks[agent_id])
                    print(f"[ORCHESTRATOR] Wired {agent_id} -> {successor_id}")
    
    # Create crew
    print("[ORCHESTRATOR] Creating crew...")
    crew = Crew(
        agents=list(agents.values()),
        tasks=list(tasks.values()),
        verbose=True
    )
    print(f"[ORCHESTRATOR] Created crew with {len(agents)} agents and {len(tasks)} tasks")
    
    # Run the crew
    print("[ORCHESTRATOR] Starting crew execution...")
    try:
        result = crew.kickoff(inputs={"topic": topic})
        print(f"[ORCHESTRATOR] Session {session_id}: Crew execution completed successfully")
        return session_id
    except Exception as e:
        print(f"[ORCHESTRATOR] Session {session_id}: Crew execution failed - {str(e)}")
        raise e
