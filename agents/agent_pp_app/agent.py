from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools import VertexAiSearchTool

import os
from agent_pp_app.tools import estandar_pp_tool
from agent_pp_app.prompts import PP_AGENT_RAG_INSTRUCTION, PP_AGENT_RAG_DESCRIPTION, PP_AGENT_BQ_INSTRUCTION, PP_AGENT_BQ_DESCRIPTION, PP_AGENT_INSTRUCTION

vertex_search_tool_pp = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_PP_ID"))
vertex_search_tool_guides = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_GUIDES_ID"))
vertex_search_tool_faq = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_FAQ_ID"))
vertex_search_tool_chileprunes_cl= VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_CHILEPRUNES_CL_ID"))

pp_agent_rag = LlmAgent(
   name="pp_agent_rag",
   model="gemini-2.0-flash-001",
   instruction=PP_AGENT_RAG_INSTRUCTION,
   description=PP_AGENT_RAG_DESCRIPTION,
   tools=[vertex_search_tool_pp,
          vertex_search_tool_guides,
          vertex_search_tool_faq,
          vertex_search_tool_chileprunes_cl],
)

pp_agent_bq = LlmAgent(
    name="pp_agent_bq",
    model="gemini-2.0-flash-001",
    instruction=PP_AGENT_BQ_INSTRUCTION,
    description=PP_AGENT_BQ_DESCRIPTION,
    tools=[estandar_pp_tool],
)

root_agent = LlmAgent(
    name="pp_agent",
    model="gemini-2.0-flash-001",
    instruction=PP_AGENT_INSTRUCTION,
    tools=[
        agent_tool.AgentTool(agent=pp_agent_rag),
        agent_tool.AgentTool(agent=pp_agent_bq)
    ]
)