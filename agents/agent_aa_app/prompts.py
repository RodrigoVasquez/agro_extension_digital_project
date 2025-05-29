def agent_aa_instruction():
    with open("agent_aa_app/prompts/agent_aa/instruction.md") as f:
        return f.read()
    
def agent_aa_bq_instruction():
    with open("agent_aa_app/prompts/agent_aa_bq/instruction.md") as f:
        return f.read()
    
def agent_aa_bq_description():
    with open("agent_aa_app/prompts/agent_aa_bq/description.md") as f:
        return f.read()
    
def agent_aa_rag_instruction():
    with open("agent_aa_app/prompts/agent_aa_rag/instruction.md") as f:
        return f.read()
    
def agent_aa_rag_description():
    with open("agent_aa_app/prompts/agent_aa_rag/description.md") as f:
        return f.read()
