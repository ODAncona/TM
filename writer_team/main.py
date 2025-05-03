import os
from dotenv import load_dotenv
from flows.thesis_flow import ThesisWritingFlow
load_dotenv()

def main():
    topic = input("Entrez le sujet de la section à générer : ")

    flow = ThesisWritingFlow()
    flow.state.topic = topic
    result = flow.kickoff()

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{topic.replace(' ', '_')}.tex")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(flow.state.final_output)

    print(f"\n🎉 Texte final sauvegardé dans : {output_path}")

if __name__ == "__main__":
    main()