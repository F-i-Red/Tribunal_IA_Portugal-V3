"""
Testes de validação de configuração.
"""

import os
import pytest
from unittest.mock import patch

from src.utils.config import Config, ConfigError


class TestConfig:
    """Testes de configuração."""

    def test_missing_api_key(self):
        """Testa erro quando API key não está definida."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError) as exc_info:
                Config.from_env()

            assert "OPENROUTER_API_KEY" in str(exc_info.value)

    def test_placeholder_api_key(self):
        """Testa erro quando API key é placeholder."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sua_chave_aqui"}, clear=True):
            with pytest.raises(ConfigError) as exc_info:
                Config.from_env()

            assert "placeholder" in str(exc_info.value).lower()

    def test_invalid_api_key_format(self):
        """Testa erro quando API key tem formato inválido."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-abc"}, clear=True):
            with pytest.raises(ConfigError) as exc_info:
                Config.from_env()

            assert "incompleta" in str(exc_info.value).lower()

    def test_valid_config(self):
        """Testa configuração válida."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "sk-or-v1-12345678901234567890123456789012",
            "MODELO": "claude-sonnet-4-6",
            "LOG_LEVEL": "DEBUG",
        }, clear=True):
            config = Config.from_env()

            assert config.modelo == "claude-sonnet-4-6"
            assert config.log_level == "DEBUG"
            assert config.max_retries == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
