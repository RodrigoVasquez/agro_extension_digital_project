# Proposal for Simplified and Centralized Configuration

## 1. Executive Summary

This document proposes a significant simplification of the application's configuration management. The goal is to refactor the primary configuration module (`whatsapp_webhook/utils/app_config.py`) into a pure data container that directly loads all necessary values from environment variables without any internal logic or string manipulation.

This change will improve code clarity, reduce complexity, and enhance both performance and testability. By making the configuration object a simple, declarative data structure, we create a single, unambiguous source of truth for all settings, making the application easier to understand and manage.

## 2. Problem Statement

The current `app_config.py` contains logic that goes beyond simple variable loading:

- **Dynamic Key Generation**: It constructs environment variable keys at runtime (e.g., `f"ESTANDAR_{self._app_suffix}_FACEBOOK_APP"`).
- **URL Construction**: It contains methods that build final URLs (e.g., `get_agent_run_url`).
- **Complex Fallbacks**: It implements fallback logic for tokens (`_get_token`).

This mixing of configuration and logic makes the module complex and tightly couples it to the naming conventions of the environment variables. It also slightly impacts performance by executing logic during the import/instantiation phase.

## 3. Proposed Solution: Pure Configuration Objects

I propose refactoring `app_config.py` to be a set of simple Pydantic or dataclass models that directly map to the environment variables defined in the deployment environment (e.g., `cicd/modules/agent/main.tf`).

### 3.1. New Configuration Structure

The new structure will consist of nested data classes that mirror the logical grouping of the variables:

```python
import os
from pydantic import BaseModel, Field
from typing import Optional

class AppSpecificConfig(BaseModel):
    facebook_app_url: Optional[str]
    app_name: Optional[str]

class AppConfig(BaseModel):
    # Global settings
    agent_url: Optional[str] = Field(alias="APP_URL")
    wsp_token: Optional[str] = Field(alias="WSP_TOKEN")
    verify_token: Optional[str] = Field(alias="VERIFY_TOKEN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # App-specific nested configurations
    aa: AppSpecificConfig
    pp: AppSpecificConfig

    class Config:
        # Allow population by field name as well as alias
        allow_population_by_field_name = True

# Function to load the config from environment variables
def load_config_from_env() -> AppConfig:
    return AppConfig(
        agent_url=os.getenv("APP_URL"),
        wsp_token=os.getenv("WSP_TOKEN"),
        verify_token=os.getenv("VERIFY_TOKEN"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        aa=AppSpecificConfig(
            facebook_app_url=os.getenv("ESTANDAR_AA_FACEBOOK_APP"),
            app_name=os.getenv("ESTANDAR_AA_APP_NAME"),
        ),
        pp=AppSpecificConfig(
            facebook_app_url=os.getenv("ESTANDAR_PP_FACEBOOK_APP"),
            app_name=os.getenv("ESTANDAR_PP_APP_NAME"),
        ),
    )

# Singleton instance to be used across the application
config = load_config_from_env()
```

### 3.2. Key Changes

1.  **No More Logic**: The configuration classes will contain only fields, not methods or properties with logic.
2.  **Direct Mapping**: Each field will correspond directly to one environment variable.
3.  **Centralized Loading**: A single function, `load_config_from_env()`, will be responsible for reading all environment variables and populating the configuration object.
4.  **Singleton Instance**: The application will import a single, pre-populated `config` object, ensuring that environment variables are read only once at startup.
5.  **Consumer Responsibility**: Modules that use the configuration will be responsible for constructing the final URLs they need (e.g., appending `/messages` or `/run`). This moves the logic closer to where it is used and decouples the configuration from the implementation details of the clients.

## 4. Benefits of the Proposed Changes

- **Reduced Complexity**: The code becomes significantly easier to read, understand, and maintain.
- **Improved Performance**: Eliminating runtime logic and string formatting during configuration loading will reduce application startup time and request latency.
- **Enhanced Testability**: It is much easier to create and inject a simple configuration data object in tests than it is to mock a class with complex logic.
- **Clearer Separation of Concerns**: The configuration module will be solely responsible for holding configuration data, while other modules will be responsible for using that data to perform their tasks.
- **Single Source of Truth**: All environment variable access is consolidated into a single function, making it easy to see at a glance what configuration the application requires.

## 5. Implementation Steps

1.  **Create `IMPROVEMENT_PROPOSAL_V3.md`**: Document the new plan (this file).
2.  **Refactor `app_config.py`**: Replace the existing classes with the new, simplified data classes and loading function.
3.  **Update Dependent Modules**: Modify all modules that currently use the configuration object to work with the new, simplified structure. This will primarily involve updating how they access configuration values and construct URLs.
4.  **Commit Changes**: Commit the refactored code to the `feature/improve-code-organization` branch.
