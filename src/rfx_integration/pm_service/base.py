from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from abc import ABC, abstractmethod

_PM_REGISTRY = {}


# Request/Response Models
class CreateTicketPayload(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    status_id: Optional[str] = None
    priority: Optional[str] = None
    labels: Optional[List[str]] = []
    project_id: Optional[str] = None
    team_id: Optional[str] = None
    ticket_id: Optional[str] = None 


class CreateTicketResponse(BaseModel):
    external_id: str
    url: str
    title: str
    status: Optional[str] = None


class UpdateTicketPayload(BaseModel):
    external_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    status_id: Optional[str] = None
    assignee_id: Optional[str] = None
    priority: Optional[int] = None


class UpdateTicketResponse(BaseModel):
    external_id: str
    updated: bool
    external_url: Optional[str] = None


class PMService(ABC):
    """Abstract base class for Project Management integrations"""
    
    __abstract__ = True
    
    def __init_subclass__(cls, **kwargs):
        if cls.__dict__.get("__abstract__", False):
            return
            
        super().__init_subclass__(**kwargs)
        provider_name = getattr(cls, 'PROVIDER_NAME', cls.__name__)
        
        if provider_name in _PM_REGISTRY:
            raise ValueError(f"PMService provider '{provider_name}' is already registered.")
        
        _PM_REGISTRY[provider_name] = cls
        print(f"Registered PMService provider: {provider_name}")
    
    def __init__(self, config: dict):
        self.config = config or {}
    
    @classmethod
    def init_client(cls, provider: str, config: dict = None):
        """Initialize a PM service client by provider name"""
        if provider not in _PM_REGISTRY:
            available = ', '.join(_PM_REGISTRY.keys())
            raise ValueError(
                f"PMService provider '{provider}' is not registered. "
                f"Available providers: {available}"
            )
        
        service_class = _PM_REGISTRY[provider]
        return service_class(config or {})
    
    @abstractmethod
    async def create_ticket(self, payload: CreateTicketPayload) -> CreateTicketResponse:
        """Create a new ticket/issue in the PM system"""
        raise NotImplementedError
    
    @abstractmethod
    async def update_ticket(self, payload: UpdateTicketPayload) -> UpdateTicketResponse:
        """Update an existing ticket/issue"""
        raise NotImplementedError
    
    @abstractmethod
    async def delete_ticket(self, external_id: str) -> bool:
        """Delete a ticket/issue"""
        raise NotImplementedError
    
    @abstractmethod
    async def get_ticket(self, external_id: str) -> Dict[str, Any]:
        """Get ticket details"""
        raise NotImplementedError