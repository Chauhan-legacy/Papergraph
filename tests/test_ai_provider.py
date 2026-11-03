"""
Tests for Modular AI Provider Engine
"""
import pytest
from app.models.schemas import AIProviderConfig
from app.providers.ai_provider import (
    LocalScientificNLPProvider,
    ExternalLLMProvider,
    AIProviderManager
)

def test_local_provider_availability():
    local_p = LocalScientificNLPProvider()
    assert local_p.is_available() is True
    # Local fallback returns None for unhandled generative prompts
    assert local_p.complete("test prompt") is None

def test_ai_provider_manager_configuration():
    manager = AIProviderManager.get_instance()
    cfg = AIProviderConfig(provider_type="local")
    manager.set_config(cfg)

    assert "Local Scientific NLP" in manager.get_active_provider_name()
    status = manager.test_connection()
    assert status["success"] is True
    assert status["provider"] == "local"

def test_external_provider_offline_handling():
    # Test that invalid port or offline Ollama server reports false cleanly without throwing
    cfg = AIProviderConfig(
        provider_type="ollama",
        base_url="http://127.0.0.1:59999",
        model_name="test-model"
    )
    provider = ExternalLLMProvider(cfg)
    assert provider.is_available() is False
    res = provider.complete("hello")
    assert res is None

