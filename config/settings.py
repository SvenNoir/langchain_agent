from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str
    app_version: str
    langsmith_tracing: str
    langsmith_endpoint: str
    langsmith_api_key: str
    langsmith_project: str
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str
    azure_openai_deployment: str

    model_config = SettingsConfigDict(env_file=".env")

env = Settings()