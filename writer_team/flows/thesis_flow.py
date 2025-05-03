from crewai.flow.flow import Flow, start, listen
from pydantic import BaseModel
from agent import ThesisArchitect, ThesisWriter, ContentExpert, LaTeXTechnician
from task import architect_task, writer_task, critic_task, technician_task
from config import get_llm

class ThesisSectionState(BaseModel):
    topic: str = ""
    outline: str = ""
    content: str = ""
    feedback: str = ""
    final_output: str = ""

class ThesisWritingFlow(Flow[ThesisSectionState]):
    @start()
    def initialize(self):
        return f"Starting thesis section generation for topic: {self.state.topic}"

    @listen(initialize)
    def create_outline(self, _):
        architect = ThesisArchitect(get_llm())
        task = architect_task(architect, self.state.topic)
        self.state.outline = task.execute()
        return self.state.outline

    @listen(create_outline)
    def human_validation_outline(self, outline):
        print("\n🔍 Outline proposé par l'architecte :")
        print(outline)
        input("✅ Valide l'outline et appuie sur Entrée pour continuer...")
        return "Outline validé par l'humain."

    @listen(human_validation_outline)
    def write_content(self, _):
        writer = ThesisWriter(get_llm())
        task = writer_task(writer)
        self.state.content = task.execute(context=self.state.outline)
        return self.state.content

    @listen(write_content)
    def critique_content(self, content):
        critic = ContentExpert(get_llm())
        task = critic_task(critic)
        self.state.feedback = task.execute(context=content)
        return self.state.feedback

    @listen(critique_content)
    def human_validation_feedback(self, feedback):
        print("\n🧐 Feedback du critique :")
        print(feedback)
        input("✅ Prends en compte le feedback et appuie sur Entrée pour continuer...")
        return "Feedback validé par l'humain."

    @listen(human_validation_feedback)
    def verify_latex(self, _):
        technician = LaTeXTechnician(get_llm())
        task = technician_task(technician)
        self.state.final_output = task.execute(context=self.state.content)
        return self.state.final_output