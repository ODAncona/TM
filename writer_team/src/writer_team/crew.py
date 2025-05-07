from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from typing import List


content_source = TextFileKnowledgeSource(
    file_paths=[
        "TM_Specification.md",
        "Input.md",
    ],
)

@CrewBase
class ThesisWritingCrew():
    """ThesisWritingCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def thesis_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['thesis_architect'],  # type: ignore[index]
            verbose=True,
            memory=True,
        )

    @agent
    def thesis_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['thesis_writer'],  # type: ignore[index]
            verbose=True,
            memory=True,

        )

    @agent
    def content_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['content_expert'],  # type: ignore[index]
            verbose=True,
            memory=False,
        )

    @agent
    def latex_technician(self) -> Agent:
        return Agent(
            config=self.agents_config['latex_technician'],  # type: ignore[index]
            verbose=True,
            memory=False,
        )

    @task
    def create_outline(self) -> Task:
        return Task(
            config=self.tasks_config['create_outline'],  # type: ignore[index]
        )

    @task
    def write_paragraphs(self) -> Task:
        return Task(
            config=self.tasks_config['write_paragraphs'],  # type: ignore[index]
        )

    @task
    def review_content(self) -> Task:
        return Task(
            config=self.tasks_config['review_content'],  # type: ignore[index]
        )

    @task
    def check_latex(self) -> Task:
        return Task(
            config=self.tasks_config['check_latex'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ThesisWritingCrew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            #memory=True,
            knowledge_sources=[
                content_source
            ],
        )
