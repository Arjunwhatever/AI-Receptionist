from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    database_url: str
    ollama_url: str = "http://localhost:11434"
    llm_model: str = "qwen3.5:9b"

settings = Settings()