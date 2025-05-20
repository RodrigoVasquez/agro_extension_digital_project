from google.adk.agents import Agent
from google.adk.tools import google_search  # Import the tool
from google.adk.tools import VertexAiSearchTool
from google.adk.agents import SequentialAgent
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset
import os
from agent_aa_app.system_prompts import ESTANDAR_AA_SYSTEM_PROMPT
from agent_aa_app.system_prompts import ESTANDAR_AA_STRUCTURED_SYSTEM_PROMPT

vertex_search_tool_structured_aa = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_STRUCTURED_AA_ID"))
vertex_search_tool_aa = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_AA_ID"))
vertex_search_tool_guides = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_GUIDES_ID"))
vertex_search_tool_faq = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_FAQ_ID"))

bigquery_toolset = ApplicationIntegrationToolset(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    connection="structured-aa-connector",
    actions=["ExecuteCustomQuery"],
    entity_operations={"estandar_aa": []}
)

#agent_structured_aa = Agent(
#   # A unique name for the agent.
#   name="agent_structured_aa",
#   # The Large Language Model (LLM) that agent will use.
#   model="gemini-2.0-flash-001", # Vertex AI Studio
#   # A short description of the agent's purpose.
#   description="Tu función principal es responder a las preguntas del usuario utilizando formato whatapps.",
#   # Instructions to set the agent's behavior.
#   instruction=ESTANDAR_AA_SYSTEM_PROMPT,
#   # Add google_search tool to perform grounding with Google search.
#   tools=[vertex_search_tool_structured_aa],
#)
#
#agent_aa = Agent(
#   name="agent_aa",
#   model="gemini-2.0-flash-001", # Vertex AI Studio
#   description="Tu función principal es responder a las preguntas del usuario utilizando formato whatapps.  Y formatea los links que retornes como hipervinculos cuando tengas que retornar un link",
#   instruction=ESTANDAR_AA_STRUCTURED_SYSTEM_PROMPT,
#   tools=[vertex_search_tool_aa],
#)
#agent_guides = Agent(
#   name="agent_guides",
#   model="gemini-2.0-flash-001", # Vertex AI Studio
#   description="Tu función principal es responder a las preguntas del usuario utilizando formato whatapps.",
#   instruction="",
#   tools=[vertex_search_tool_guides],
#)
#
#agent_faq = Agent(
#   name="agent_faq",
#   model="gemini-2.0-flash-001", # Vertex AI Studio
#   description="Tu función principal es responder a las preguntas del usuario utilizando formato whatapps. Y formatea los links que retornes como hipervinculos",
#   instruction="",
#   tools=[vertex_search_tool_faq],
#)
#

#root_agent = LlmAgent(
#    name="Coordinator",
#    model="gemini-2.0-flash",
#    description="TU funcion es coordinar los agentes y retornar la respuesta al usuario en formato whatapps si es que puedes", 
#    sub_agents=[ # Assign sub_agents here
#        agent_aa, agent_structured_aa
#    ]
#)
#

root_agent = Agent(
   # A unique name for the agent.
   name="agent_structured_aa",
   # The Large Language Model (LLM) that agent will use.
   model="gemini-2.0-flash-001", # Vertex AI Studio
   # A short description of the agent's purpose.
   description="Tu función principal es responder a las preguntas del usuario utilizando formato whatapps.",
   # Instructions to set the agent's behavior.
   #instruction=ESTANDAR_AA_SYSTEM_PROMPT,
   instruction="eres capaz de responder con links y acciones para el estandar",

   # Add google_search tool to perform grounding with Google search.
   tools=bigquery_toolset.get_tools()
)