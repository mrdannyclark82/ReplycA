import os
from openai import OpenAI
from .skill_manager import execute_skill, list_skills
client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1"
)
def register():
    return {
        "name": "grok_master",
        "description": "xAI Grok orchestrator",
        "version": "1.0.0",
        "commands": ["/grok"],
        "requires": ["openai"],
    }
def execute(payload):
    query = payload.get("query", "")
    
    # Decide route
    skills = list_skills()
    decide_prompt = f"Query: {query}\nSkills: {skills}\nJSON: {{\"direct\": true}} or {{\"skill\": \"name\", \"sub\": \"query\"}}"
    decision = client.chat.completions.create(
        model="grok-beta",
        messages=[{"role": "user", "content": decide_prompt}]
    ).choices[0].message.content
    
    try:
        sub = eval(decision)  # safe eval or json.loads
        if sub.get("skill"):
            return execute_skill(sub["skill"], {"query": sub["sub"]})
    except:
        pass
    
    # Direct Grok
    resp = client.chat.completions.create(model="grok-beta", messages=[{"role": "user", "content": query}])
    return {"direct": resp.choices[0].message.content.content}