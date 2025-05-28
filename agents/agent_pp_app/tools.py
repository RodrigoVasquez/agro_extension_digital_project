import os
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset

estandar_pp_tool = ApplicationIntegrationToolset(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    connection=os.getenv("BIGQUERY_INTEGRATION_APPLICATION_CONNECTOR_ID"),
    actions=["ExecuteCustomQuery"],
    entity_operations={"estandar_pp": ["LIST"]},
    tool_instructions="Útil para consultar rápidamente y de forma interactiva cualquier detalle dentro de un catálogo estructurado de estándares y buenas prácticas, permitiendo a los usuarios obtener respuestas precisas sobre criterios específicos identificados por sus códigos o características categóricas como nivel de importancia, dimensión o tema. Facilita la comprensión de las acciones concretas a implementar, los métodos de verificación necesarios, la puntuación asociada a cada elemento o los recursos de apoyo disponibles, convirtiéndose en una ayuda esencial para quienes necesitan navegar, interpretar o aplicar dicho marco normativo o de certificación de manera eficiente."
)