import subprocess
from .skill_docker_bash import execute as bash_exec  # chain
def register():
    return {"name": "code_analyze", "commands": ["/analyze"]}
def execute(payload):
    path = payload.get("path", ".")
    cmd = f"grep -r '{payload.get('pattern', '')}' {path} || find {path} -name '*.py'"
    return bash_exec({"cmd": cmd})  # sandboxed