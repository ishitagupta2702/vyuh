from crewai import Agent, Crew, Process, Task

from crewai.project import CrewBase, agent, crew, task
from langchain_community.chat_models import ChatLiteLLM
import os

from dotenv import load_dotenv
load_dotenv()

# Set environment variables for API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

# Import development tools
from .tools.development_tools import formatter_tool, improver_tool, write_tool, read_tool, storage_tool

@CrewBase
class DevelopmentCrew:
    """Development Crew that takes an app idea and produces a complete source code repo"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    @agent
    def idea_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['idea_agent'],
            llm=ChatLiteLLM(model="gpt-4"),
            tools=[formatter_tool, storage_tool],
            verbose=True
        )

    @agent
    def architect_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['architect_agent'],
            llm=ChatLiteLLM(model="gpt-4"),
            tools=[formatter_tool, improver_tool, storage_tool],
            verbose=True
        )

    @agent
    def backend_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_agent'],
            llm=ChatLiteLLM(model="gpt-4"),
            tools=[write_tool, formatter_tool, improver_tool, storage_tool],
            verbose=True
        )

    @agent
    def frontend_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_agent'],
            llm=ChatLiteLLM(model="gpt-4"),
            tools=[write_tool, formatter_tool, improver_tool, storage_tool],
            verbose=True
        )

    @agent
    def qa_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['qa_agent'],
            llm=ChatLiteLLM(model="gpt-4"),
            tools=[read_tool, formatter_tool, improver_tool, storage_tool],
            verbose=True
        )

    @agent
    def packager_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['packager_agent'],
            llm=ChatLiteLLM(model="gpt-4"),
            tools=[write_tool, formatter_tool, storage_tool],
            verbose=True
        )

    @task
    def idea_task(self) -> Task:
        return Task(
            config=self.tasks_config['idea_task'],
            agent=self.idea_agent()
        )

    @task
    def architecture_task(self) -> Task:
        return Task(
            config=self.tasks_config['architecture_task'],
            agent=self.architect_agent()
        )

    @task
    def backend_task(self) -> Task:
        return Task(
            config=self.tasks_config['backend_task'],
            agent=self.backend_agent()
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],
            agent=self.frontend_agent()
        )

    @task
    def qa_task(self) -> Task:
        return Task(
            config=self.tasks_config['qa_task'],
            agent=self.qa_agent()
        )

    @task
    def packaging_task(self) -> Task:
        return Task(
            config=self.tasks_config['packaging_task'],
            agent=self.packager_agent()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the sequential development crew"""
        return Crew(
            agents=[
                self.idea_agent(),
                self.architect_agent(),
                self.backend_agent(),
                self.frontend_agent(),
                self.qa_agent(),
                self.packager_agent()
            ],
            tasks=[
                self.idea_task(),
                self.architecture_task(),
                self.backend_task(),
                self.frontend_task(),
                self.qa_task(),
                self.packaging_task()
            ],
            description="Development Crew that takes an app idea and produces a complete source code repo",
            verbose=True
        )

# Keep the original publishCrew for backward compatibility
@CrewBase
class publishCrew:
    """Publishing House Crew (Legacy)"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=ChatLiteLLM(model="gpt-3.5-turbo"),
            verbose=True
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer'],
            llm=ChatLiteLLM(model="gpt-3.5-turbo"),
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            agent=self.researcher()
        )

    @task
    def blog_task(self) -> Task:
        return Task(
            config=self.tasks_config['blog_task'],
            agent=self.writer()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the crew"""
        return Crew(
            agents=[self.researcher(), self.writer()],
            tasks=[self.research_task(), self.blog_task()]
        )

if __name__ == "__main__":
    # Test the development crew
    development_crew = DevelopmentCrew()
    result = development_crew.crew().kickoff(inputs={"input_idea": "A task management app for remote teams"})
    print(result)
