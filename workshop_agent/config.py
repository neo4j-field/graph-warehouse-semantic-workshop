"""Configuration for the workshop agent. The only module that reads ``.env``."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DEFAULT_AGENT_MODEL = "gpt-4o-mini"
DEFAULT_ROW_LIMIT = 50

# Env vars forwarded to the neocarta-mcp subprocess (it embeds search queries).
_MCP_ENV_PREFIXES = (
    "NEO4J_",
    "EMBEDDING_",
    "OPENAI_",
    "OLLAMA_",
    "GEMINI_",
    "COHERE_",
    "AZURE_",
    "AWS_",
    "CORPORATE_GATEWAY_",
)


def parse_gateway_headers(raw: str | None) -> dict[str, str]:
    """Parse ``CORPORATE_GATEWAY_HEADERS`` (a JSON object); empty on absent/invalid."""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"CORPORATE_GATEWAY_HEADERS is not valid JSON, ignoring: {e}")
        return {}
    if not isinstance(data, dict):
        logger.warning("CORPORATE_GATEWAY_HEADERS must be a JSON object, ignoring")
        return {}
    return {str(k): str(v) for k, v in data.items()}


@dataclass
class Settings:
    """Resolved agent settings."""

    agent_model: str = DEFAULT_AGENT_MODEL
    gateway_headers: dict[str, str] = field(default_factory=dict)
    row_limit: int = DEFAULT_ROW_LIMIT
    snowflake: dict[str, Any] = field(default_factory=dict)
    neo4j: dict[str, Any] = field(default_factory=dict)
    mcp_env: dict[str, str] = field(default_factory=dict)

    @property
    def litellm_kwargs(self) -> dict[str, Any]:
        """Extra kwargs for LiteLLM calls (custom gateway headers)."""
        return {"extra_headers": self.gateway_headers} if self.gateway_headers else {}


def _snowflake_kwargs(env: Any) -> dict[str, Any]:
    """Build snowflake.connector kwargs: key-pair > authenticator > password."""
    kw: dict[str, Any] = {
        "account": env.get("SNOWFLAKE_ACCOUNT"),
        "user": env.get("SNOWFLAKE_USER"),
        "warehouse": env.get("SNOWFLAKE_WAREHOUSE"),
        "database": env.get("SNOWFLAKE_DATABASE"),
        "schema": env.get("SNOWFLAKE_SCHEMA"),
        "login_timeout": 30,
        "network_timeout": 60,
    }
    if env.get("SNOWFLAKE_ROLE"):
        kw["role"] = env["SNOWFLAKE_ROLE"]
    if env.get("SNOWFLAKE_PRIVATE_KEY_PATH"):
        from cryptography.hazmat.primitives import serialization

        pw = env.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
        key = serialization.load_pem_private_key(
            Path(env["SNOWFLAKE_PRIVATE_KEY_PATH"]).read_bytes(),
            password=pw.encode() if pw else None,
        )
        kw["private_key"] = key.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    elif env.get("SNOWFLAKE_AUTHENTICATOR"):
        kw["authenticator"] = env["SNOWFLAKE_AUTHENTICATOR"]
        if env.get("SNOWFLAKE_TOKEN"):
            kw["token"] = env["SNOWFLAKE_TOKEN"]
    else:
        kw["password"] = env.get("SNOWFLAKE_PASSWORD")
    return {k: v for k, v in kw.items() if v is not None}


def _neo4j_kwargs(env: Any) -> dict[str, Any]:
    """Build connection settings for the read-only Cypher tool."""
    return {
        "uri": env.get("NEO4J_URI"),
        "auth": (env.get("NEO4J_USERNAME"), env.get("NEO4J_PASSWORD")),
        "database": env.get("NEO4J_DATABASE", "neo4j"),
    }


def load_settings(env_file: Path | None = None) -> Settings:
    """Load ``.env`` once and resolve settings from the environment."""
    load_dotenv(env_file or Path.cwd() / ".env")
    env = os.environ
    return Settings(
        agent_model=env.get("AGENT_MODEL", DEFAULT_AGENT_MODEL),
        gateway_headers=parse_gateway_headers(env.get("CORPORATE_GATEWAY_HEADERS")),
        row_limit=int(env.get("AGENT_ROW_LIMIT", DEFAULT_ROW_LIMIT)),
        snowflake=_snowflake_kwargs(env),
        neo4j=_neo4j_kwargs(env),
        mcp_env={
            k: v
            for k, v in env.items()
            if k.startswith(_MCP_ENV_PREFIXES) or k == "PATH"
        },
    )
