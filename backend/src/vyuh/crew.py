from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_community.chat_models import ChatLiteLLM
import os
import sys
from pathlib import Path

# Add sandbox path to import sandbox tools
project_root = Path(__file__).parent.parent.parent
sandbox_path = project_root / "sandbox"
sys.path.insert(0, str(sandbox_path))

from dotenv import load_dotenv
load_dotenv()

# Set environment variables for API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

@CrewBase
class publishCrew:
    """Publishing House Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    @agent
    def researcher(self) -> Agent:
        agent = Agent(
            config=self.agents_config['researcher'],
            llm=ChatLiteLLM(model="gpt-3.5-turbo"),
            verbose=True
        )
        
        # Add sandbox tools to researcher
        try:
            from crewai_tools import create_file_tool, create_command_tool
            # Note: You'll need to pass sandbox_manager when creating tools
            # agent.tools = [create_file_tool(sandbox_manager), create_command_tool(sandbox_manager)]
        except ImportError:
            pass  # Sandbox tools not available
        
        return agent

    @agent
    def writer(self) -> Agent:
        agent = Agent(
            config=self.agents_config['writer'],
            llm=ChatLiteLLM(model="gpt-3.5-turbo"),
            verbose=True
        )
        
        # Add sandbox tools to writer
        try:
            from crewai_tools import create_file_tool, create_pdf_tool
            # Note: You'll need to pass sandbox_manager when creating tools
            # agent.tools = [create_file_tool(sandbox_manager), create_pdf_tool(sandbox_manager)]
        except ImportError:
            pass  # Sandbox tools not available
        
        return agent

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            agent = self.researcher()
        )

    @task
    def blog_task(self) -> Task:
        return Task(
            config=self.tasks_config['blog_task'],
            agent = self.writer()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the crew"""
        return Crew(
            agents=[self.researcher(), self.writer()],
            tasks=[self.research_task(), self.blog_task()]
        )

if __name__ == "__main__":
    publish_crew = publishCrew()
    publish_crew.crew().kickoff(inputs={"topic": "The future of content creation"})