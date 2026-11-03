"""
Literature Provider Abstract Base Class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class LiteratureProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of literature data provider."""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        filter_type: str = "all",
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search literature and return standardized results."""
        pass

    @abstractmethod
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single paper metadata by provider ID or DOI."""
        pass

