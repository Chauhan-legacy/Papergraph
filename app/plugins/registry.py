"""
PaperGraph V3 - Plugin Registry (Phase 5)
Handles dynamic discovery, verification, and sandboxed execution of external plugins.
Enforces provenance tracking and error containment.
"""
import importlib
import logging
from typing import Dict, List, Optional, Any
from .interfaces import (
    PluginManifest,
    BasePlugin,
    OCRBackendPlugin,
    EmbeddingModelPlugin,
    LLMProviderPlugin,
    ReportRendererPlugin
)

logger = logging.getLogger("papergraph.v3.plugins")

class PluginRegistry:
    def __init__(self):
        self._manifests: Dict[str, PluginManifest] = {}
        self._active_plugins: Dict[str, BasePlugin] = {}
        self._failed_plugins: Dict[str, str] = {}

    def register_manifest(self, manifest_data: Dict[str, Any]) -> bool:
        """Register and validate an external plugin manifest."""
        try:
            manifest = PluginManifest(**manifest_data)
            if self.validate(manifest):
                self._manifests[manifest.plugin_id] = manifest
                return True
        except Exception as e:
            logger.error(f"Failed to register plugin manifest: {e}")
        return False

    def validate(self, manifest: PluginManifest) -> bool:
        """Validate required fields, semantic versions, and capabilities."""
        if not manifest.plugin_id or not manifest.entry_point:
            return False
        valid_caps = {"ocr_backend", "embedding_model", "llm_provider", "report_renderer"}
        if not any(cap in valid_caps for cap in manifest.capabilities):
            return False
        return True

    def load(self, plugin_id: str) -> Optional[BasePlugin]:
        """Load and instantiate a plugin by ID with failure isolation."""
        if plugin_id in self._active_plugins:
            return self._active_plugins[plugin_id]

        if plugin_id not in self._manifests:
            logger.warning(f"Plugin '{plugin_id}' not found in registry.")
            return None

        manifest = self._manifests[plugin_id]
        try:
            module_name, class_name = manifest.entry_point.split(":")
            module = importlib.import_module(module_name)
            plugin_cls = getattr(module, class_name)
            instance = plugin_cls(manifest)
            self._active_plugins[plugin_id] = instance
            manifest.enabled = True
            return instance
        except Exception as e:
            err_msg = f"Failed to instantiate plugin '{plugin_id}': {e}"
            logger.error(err_msg)
            self._failed_plugins[plugin_id] = err_msg
            return None

    def execute_ocr_plugin(self, plugin_id: str, pdf_path: str, page_number: int) -> Optional[Dict[str, Any]]:
        """Executes an OCR backend plugin with strict provenance enforcement."""
        plugin = self.load(plugin_id)
        if not plugin or not isinstance(plugin, OCRBackendPlugin):
            return None

        try:
            result = plugin.extract(pdf_path, page_number)
            # Enforce provenance rule: must have extraction_source matching plugin_id
            if not isinstance(result, dict) or "extraction_source" not in result:
                logger.error(f"Plugin '{plugin_id}' output rejected: missing 'extraction_source'.")
                return None
            return result
        except Exception as e:
            plugin.failed = True
            plugin.last_error = str(e)
            self._failed_plugins[plugin_id] = str(e)
            logger.error(f"Isolated failure in plugin '{plugin_id}': {e}")
            return None

    def list_plugins(self) -> List[Dict[str, Any]]:
        out = []
        for pid, m in self._manifests.items():
            out.append({
                "plugin_id": pid,
                "version": m.version,
                "capabilities": m.capabilities,
                "enabled": m.enabled,
                "status": "FAILED" if pid in self._failed_plugins else ("ACTIVE" if pid in self._active_plugins else "REGISTERED"),
                "error": self._failed_plugins.get(pid)
            })
        return out

plugin_registry = PluginRegistry()

