import os

def generate_readme(project_name, description, installation_instructions, usage_examples, additional_info=""):
    readme_content = f"# {project_name}\n\n"
    readme_content += f"## Description\n{description}\n\n"
    readme_content += "## Installation\n"
    readme_content += "\n".join([f"- {instruction}" for instruction in installation_instructions])
    readme_content += "\n\n## Usage\n"
    readme_content += "\n".join([f"- {example}" for example in usage_examples])
    if additional_info:
        readme_content += f"\n\n## Additional Information\n{additional_info}"
    
    with open("README.md", "w") as file:
        file.write(readme_content)

    return "README.md has been generated successfully."

generate_readme(
    project_name="Qwen Assistant",
    description="An AI assistant capable of executing various tasks using different tools.",
    installation_instructions=[
        "Clone the repository",
        "Install dependencies using pip install -r requirements.txt"
    ],
    usage_examples=[
        "Run the assistant using python main.py",
        "Use the terminal_executor tool to run commands"
    ],
    additional_info="For more information, refer to the documentation."
)