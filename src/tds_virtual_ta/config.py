#### File 4: Update `src/tds_virtual_ta/config.py`

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings - reads from HF Spaces Secrets."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Service Configuration
    service_secret: str = Field(...)
    service_host: str = Field(default="0.0.0.0")
    service_port: int = Field(default=7860)  # HF Spaces uses 7860
    
    # Task Configuration
    task_timeout: int = Field(default=570)
    callback_timeout: int = Field(default=30)
    
    # LLM Configuration
    aipipe_api_key: str = Field(...)
    aipipe_base_url: str = Field(default="https://api.aipipe.ai/v1")
    aipipe_model: str = Field(default="gpt-4")
    
    # HuggingFace Configuration
    hf_token: str = Field(...)
    hf_inference_model: str = Field(default="meta-llama/Llama-3.2-3B-Instruct")
    hf_inference_url: str = Field(default="https://api-inference.huggingface.co/models")
    
    # GitHub Configuration
    github_token: str = Field(...)
    github_username: str = Field(...)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    # Security
    enable_code_validation: bool = Field(default=True)
    max_repo_name_length: int = Field(default=100)
    max_retries: int = Field(default=5)
    retry_backoff_factor: float = Field(default=2.0)
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return v_upper


settings = Settings()