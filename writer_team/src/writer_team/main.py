#!/usr/bin/env python
import sys
import warnings
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
from writer_team.crew import ThesisWritingCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    inputs = {
        'section_topic': 'Declarative vs Imperative Configuration',
        'current_year': str(datetime.now().year),
        'description': 'Write a subsection of a thesis based on the given topic.',
    }


    try:
        ThesisWritingCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    run()