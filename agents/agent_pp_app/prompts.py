def agent_pp_instruction():
    with open("agent_pp_app/prompts/agent_pp/instruction.md") as f:
        return f.read()
    
def agent_pp_bq_instruction():
    with open("agent_pp_app/prompts/agent_pp_bq/instruction.md") as f:
        return f.read()
    
def agent_pp_bq_description():
    with open("agent_pp_app/prompts/agent_pp_bq/description.md") as f:
        return f.read()
    
def agent_pp_rag_instruction():
    with open("agent_pp_app/prompts/agent_pp_rag/instruction.md") as f:
        return f.read()
    
def agent_pp_rag_description():
    with open("agent_pp_app/prompts/agent_pp_rag/description.md") as f:
        return f.read()