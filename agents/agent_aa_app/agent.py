from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools import VertexAiSearchTool

import os, time
from agent_aa_app.tools import estandar_aa_tool
from agent_aa_app.prompts import agent_aa_instruction, agent_aa_bq_instruction, agent_aa_bq_description, agent_aa_rag_instruction, agent_aa_rag_description
vertex_search_tool_aa = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_AA_ID"))
vertex_search_tool_guides = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_GUIDES_ID"))
vertex_search_tool_faq = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_FAQ_ID"))
vertex_search_tool_chileprunes_cl= VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_CHILEPRUNES_CL_ID"))

aa_agent_rag = LlmAgent(
   name="aa_agent_rag",
   model="gemini-2.0-flash-001",
   instruction=agent_aa_rag_instruction(),
   description=agent_aa_rag_description(),
   tools=[vertex_search_tool_aa,
          vertex_search_tool_guides,
          vertex_search_tool_faq,
          vertex_search_tool_chileprunes_cl],
)

aa_agent_bq = LlmAgent(
    name="aa_agent_bq",
    model="gemini-2.0-flash-001",
    instruction=agent_aa_bq_instruction(),
    description=agent_aa_bq_description(),
    tools= [estandar_aa_tool],
)

root_agent = LlmAgent(
    name="aa_agent",
    model="gemini-2.0-flash-001",
    instruction=agent_aa_instruction(),
    tools=[
        agent_tool.AgentTool(agent=aa_agent_rag),
        agent_tool.AgentTool(agent=aa_agent_bq)
    ]
)