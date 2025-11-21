from operator import le
from signal import default_int_handler
from this import d
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import Optional, List, Union
import os
import secrets
from pathlib import Path


class Settings(BaseSettings):

    # APP Info
    app_name: str = Field(
        default= "API"
    )
    app_version: str = Field(
        default="0.1.0"
    )
    environment: str = Field(
        default="development"
    )
    # Sever Settings
    host: str = Field(
        default="127.0.0.1",
        description="Sever host address"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Sever port number"
    )
    # MCP Settings
    mcp1_host: str = Field(
        default="127.0.0.1",
        description="MCP server host address"
    )
    mcp1_port: int = Field(
        default=8001,
        ge=1,
        le=65535,
        description="MCP server port number"
    )
    mcp2_host: str = Field(
        default="127.0.0.1",
        description="MCP server host address"
    )
    mcp2_port: int = Field(
        default=8006,
        ge=1,
        le=65535,
        description="MCP server port number"
    )

    mcp_transport: str = Field(
        default="sse",
        pattern="^(stdio|sse|streamable-http)$",
        description="MCP transport protocol"
    )
    # External APIs
    external_api_url: Optional[str] = Field(
        default=None,
        description="External API base URL"
    )
    external_api_key: Optional[str] = Field(
        default=None,
        description="External API key"
    )

    # CORS Settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Allowed CORS origins (comma-separated)"
    )
    cors_methods: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS",
        description="Allowed CORS methods (comma-separated)"
    )

class DevelopmentSettings(Settings):
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:8080,http://localhost:8081,http://127.0.0.1:3000,http://127.0.0.1:8080"



def get_settings() -> Settings:
    env = os.getenv("ENVIRONMENT") or os.getenv("ENV","development")
    env = env.lower().strip()

    return DevelopmentSettings()




# Global settings instance
settings = get_settings()