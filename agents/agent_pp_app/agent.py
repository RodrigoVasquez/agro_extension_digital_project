from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools import VertexAiSearchTool

import os
from agent_pp_app.tools import estandar_pp_tool
from agent_pp_app.prompts import agent_pp_instruction, agent_pp_bq_instruction, agent_pp_bq_description, agent_pp_rag_instruction, agent_pp_rag_description

vertex_search_tool_pp = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_PP_ID"))
vertex_search_tool_guides = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_GUIDES_ID"))
vertex_search_tool_faq = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_FAQ_ID"))
vertex_search_tool_chileprunes_cl= VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_CHILEPRUNES_CL_ID"))

pp_agent_rag = LlmAgent(
   name="pp_agent_rag",
   model="gemini-2.5-flash",
   instruction=agent_pp_rag_instruction(),
   description=agent_pp_rag_description(),
   tools=[vertex_search_tool_pp,
          vertex_search_tool_guides,
          vertex_search_tool_faq,
          vertex_search_tool_chileprunes_cl],
)

pp_agent_bq = LlmAgent(
    name="pp_agent_bq",
    model="gemini-2.5-flash",
    instruction=agent_pp_bq_instruction(),
    description=agent_pp_bq_description(),
    tools=[estandar_pp_tool],
)

root_agent = LlmAgent(
    name="pp_agent",
    model="gemini-2.5-pro",
    instruction=agent_pp_instruction(),
    tools=[
        agent_tool.AgentTool(agent=pp_agent_rag),
        agent_tool.AgentTool(agent=pp_agent_bq)
    ]
)
