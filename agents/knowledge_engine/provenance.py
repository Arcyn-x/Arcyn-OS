"""
Provenance module for Knowledge Engine.

Tracks source agent, timestamps, and version references for all knowledge items.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class Provenance:
    """
    Tracks provenance metadata for knowledge items.
    
    Responsibilities:
    - Track source agent
    - Track timestamps
    - Track version references
    - Attach provenance to every knowledge item
    
    This is non-negotiable.
    
    TODO: Add digital signatures for verification
    TODO: Implement provenance chains
    TODO: Add integrity checks
    """
    
    def __init__(self, source_agent: str, source_version: Optional[str] = None):
        """
        Initialize provenance tracker.
        
        Args:
            source_agent: Name of the agent that created this knowledge
            source_version: Optional version of the source agent
        """
        self.source_agent = source_agent
        self.source_version = source_version or "1.0.0"
        self.created_at = datetime.now().isoformat()
        self.provenance_id = str(uuid.uuid4())
    
    def create(self, additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create provenance metadata.
        
        Args:
            additional_metadata: Optional additional metadata to include
        
        Returns:
            Provenance dictionary
        """
        provenance = {
            "provenance_id": self.provenance_id,
            "source_agent": self.source_agent,
            "source_version": self.source_version,
            "created_at": self.created_at,
            "created_timestamp": datetime.now().timestamp()
        }
        
        if additional_metadata:
            provenance["metadata"] = additional_metadata
        
        return provenance
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Provenance':
        """
        Create Provenance instance from dictionary.
        
        Args:
            data: Provenance dictionary
        
        Returns:
            Provenance instance
        """
        source_agent = data.get("source_agent", "unknown")
        source_version = data.get("source_version")
        
        prov = Provenance(source_agent, source_version)
        prov.provenance_id = data.get("provenance_id", prov.provenance_id)
        prov.created_at = data.get("created_at", prov.created_at)
        
        return prov
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert provenance to dictionary.
        
        Returns:
            Provenance dictionary
        """
        return {
            "provenance_id": self.provenance_id,
            "source_agent": self.source_agent,
            "source_version": self.source_version,
            "created_at": self.created_at,
            "created_timestamp": datetime.now().timestamp()
        }
    
    def add_reference(self, reference_type: str, reference_id: str) -> Dict[str, Any]:
        """
        Add a reference to another knowledge item.
        
        Args:
            reference_type: Type of reference (e.g., "depends_on", "derived_from")
            reference_id: ID of the referenced item
        
        Returns:
            Updated provenance dictionary
        """
        prov_dict = self.to_dict()
        
        if "references" not in prov_dict:
            prov_dict["references"] = []
        
        prov_dict["references"].append({
            "type": reference_type,
            "id": reference_id,
            "added_at": datetime.now().isoformat()
        })
        
        return prov_dict
    
    def verify(self, expected_agent: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Verify provenance integrity.
        
        Args:
            expected_agent: Optional expected source agent
        
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        if not self.source_agent:
            return False, "Missing source agent"
        
        if not self.created_at:
            return False, "Missing creation timestamp"
        
        if expected_agent and self.source_agent != expected_agent:
            return False, f"Source agent mismatch: expected {expected_agent}, got {self.source_agent}"
        
        return True, None

