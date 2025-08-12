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
            from crewai_tools import SandboxContextManager
            # Note: Sandbox tools will be initialized when the crew runs
            # Tools are managed by the crew execution context
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
            from crewai_tools import SandboxContextManager
            # Note: Sandbox tools will be initialized when the crew runs
            # Tools are managed by the crew execution context
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
    
    async def run_with_sandbox(self, topic: str) -> dict:
        """Run the crew with Daytona sandbox tools properly initialized."""
        try:
            from crewai_tools import SandboxContextManager
            
            # Create sandbox context manager
            async with SandboxContextManager() as sandbox_ctx:
                # Get tools for each agent
                tools = sandbox_ctx.get_tools()
                
                # Create agents with tools
                researcher = self.researcher()
                researcher.tools = [tools["file_tool"], tools["command_tool"]]
                
                writer = self.writer()
                writer.tools = [tools["file_tool"], tools["pdf_tool"]]
                
                # Create crew with tools
                crew = Crew(
                    agents=[researcher, writer],
                    tasks=[self.research_task(), self.blog_task()]
                )
                
                # Execute crew
                result = crew.kickoff(inputs={"topic": topic})
                
                return {
                    "success": True,
                    "result": result,
                    "sandbox_status": sandbox_ctx.get_sandbox_status()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sandbox_status": "failed"
            }

if __name__ == "__main__":
    publish_crew = publishCrew()
    publish_crew.crew().kickoff(inputs={"topic": "The future of content creation"})