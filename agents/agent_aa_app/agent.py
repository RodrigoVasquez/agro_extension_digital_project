from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools import VertexAiSearchTool

import os
from agent_aa_app.system_prompts import ESTANDAR_AA_SYSTEM_PROMPT
from agent_aa_app.system_prompts import ESTANDAR_AA_STRUCTURED_SYSTEM_PROMPT
from agent_aa_app.tools import estandar_aa_tool

vertex_search_tool_aa = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_AA_ID"))
vertex_search_tool_guides = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_GUIDES_ID"))
vertex_search_tool_faq = VertexAiSearchTool(data_store_id=os.getenv("DATASTORE_FAQ_ID"))

aa_agent_rag = LlmAgent(
   name="aa_agent_rag",
   model="gemini-2.0-flash-001",
   description="Tu función principal es responder a las preguntas del usuario utilizando formato whatapps.  Y formatea los links que retornes como hipervinculos cuando tengas que retornar un link",
   instruction=ESTANDAR_AA_STRUCTURED_SYSTEM_PROMPT,
   tools=[vertex_search_tool_aa,
          vertex_search_tool_guides,
          vertex_search_tool_faq],
)

root_agent = LlmAgent(
   name="aa_agent_bq", # Vertex AI Studio
   model="gemini-2.0-flash-001",
   description="Útil para consultar rápidamente y de forma interactiva cualquier detalle dentro de un catálogo estructurado de estándares y buenas prácticas, permitiendo a los usuarios obtener respuestas precisas sobre criterios específicos identificados por sus códigos o características categóricas como nivel de importancia, dimensión o tema. Facilita la comprensión de las acciones concretas a implementar, los métodos de verificación necesarios, la puntuación asociada a cada elemento o los recursos de apoyo disponibles, convirtiéndose en una ayuda esencial para quienes necesitan navegar, interpretar o aplicar dicho marco normativo o de certificación de manera eficiente.",
   instruction="Help user, leverage the tools you have access to",
   tools=estandar_aa_tool.get_tools(),
)

#root_agent = LlmAgent(
#    name="aa_agent",
#    model="gemini-2.0-flash-001",
#    description="TU funcion es coordinar los agentes y retornar la respuesta al usuario en formato whatapps si es que puedes",
#    instruction="TU funcion es coordinar los agentes y retornar la respuesta al usuario en formato whatapps si es que puedes",
#    tools=[
#        #agent_tool.AgentTool(agent=aa_agent_rag),
#        agent_tool.AgentTool(agent=aa_agent_bq)
#    ]
#)