import docker
import re
import os
client = docker.from_env()
def register():
    return {"name": "docker_bash", "commands": ["/bash"], "requires": ["docker"]}
def execute(payload):
    cmd = payload.get("cmd", "")
    # Validate safe: no docker/rm/mv dangerous
    if re.search(r'(rm|docker|sudo|mv\s+.*\/|\/bin\/sh)', cmd):
        return {"error": "Unsafe cmd"}
    
    vol = f"{os.getcwd()}:/wd"
    try:
        res = client.containers.run("ubuntu:22.04", f"bash -c '{cmd}'", 
                                   volumes={vol: {"bind": vol, "mode": "ro"}},
                                   remove=True, detach=False)
        return {"stdout": res.decode()}
    except Exception as e:
        return {"error": str(e)}