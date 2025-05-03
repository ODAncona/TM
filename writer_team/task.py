from crewai import Task

def architect_task(agent, section_topic):
    return Task(
        description=f"""
        Create a detailed academic outline for the thesis section "{section_topic}".
        Include:
        - Introduction
        - Main arguments and logical flow
        - Transitions between arguments
        Await human approval before proceeding.
        """,
        agent=agent
    )

def writer_task(agent):
    return Task(
        description="Write clear, structured academic paragraphs based on the approved outline.",
        agent=agent
    )

def critic_task(agent):
    return Task(
        description="Critically evaluate the written content, identifying logical flaws or weak assumptions. Provide constructive feedback.",
        agent=agent
    )

def technician_task(agent):
    return Task(
        description="Verify LaTeX formatting, ensuring correct environments, equations, citations, and adherence to academic standards.",
        agent=agent
    )