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


#============ Project Payload==========

class CreateProjectPayload(BaseModel):
    """Payload for creating project in PM service"""
    name: str
    description: Optional[str] = None
    team_id: Optional[str] = None
    lead_id: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    state: Optional[str] = None  # "PLANNED", "STARTED", "COMPLETED", etc.
    start_date: Optional[str] = None  # ISO date string
    target_date: Optional[str] = None  # ISO date string
    project_id: Optional[str] = None  # Internal project ID
    
    


class CreateProjectResponse(BaseModel):
    """Response from creating project"""
    external_id: str
    url: str
    name: str
    state: Optional[str] = None


class UpdateProjectPayload(BaseModel):
    """Payload for updating project"""
    external_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    lead_id: Optional[str] = None
    state: Optional[str] = None
    color: Optional[str] = None
    target_date: Optional[str] = None
    
    


class UpdateProjectResponse(BaseModel):
    """Response from updating project"""
    external_id: str
    updated: bool
    external_url: Optional[str] = None
    
    
# =========== Project Milestone Payload ==========
class CreateProjectMilestonePayload(BaseModel):
    """Payload for creating project milestone"""
    name: str
    project_id: str
    description: Optional[str] = None
    target_date: Optional[str] = None  # ISO date
    sort_order: Optional[float] = None


class CreateProjectMilestoneResponse(BaseModel):
    """Response after creating project milestone"""
    external_id: str
    name: str
    project_id: str
    target_date: Optional[str] = None
    external_url: Optional[str] = None


class UpdateProjectMilestonePayload(BaseModel):
    """Payload for updating project milestone"""
    external_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[str] = None
    sort_order: Optional[float] = None


class UpdateProjectMilestoneResponse(BaseModel):
    """Response after updating project milestone"""
    external_id: str
    updated: bool
    external_url: Optional[str] = None
    
    
# ========== COMMENT PAYLOAD ==========

class CreateCommentPayload(BaseModel):
    """Payload for creating comment in PM service"""
    body: str
    target_id: str  # Linear issue/ticket ID
    comment_id: Optional[str] = None  # Internal comment ID
    parent_id: Optional[str] = None
    resource_type: Optional[str] = None  # For nested comments


class CreateCommentResponse(BaseModel):
    """Response after creating comment"""
    external_id: str
    url: Optional[str] = None
    body: str


class UpdateCommentPayload(BaseModel):
    """Payload for updating comment"""
    external_id: str
    body: str


class UpdateCommentResponse(BaseModel):
    """Response after updating comment"""
    external_id: str
    updated: bool
    url: Optional[str] = None


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
    
    #======== Project Methods ========
    @abstractmethod
    async def create_project(self, payload: CreateProjectPayload) -> CreateProjectResponse:
        raise NotImplementedError
    
    @abstractmethod
    async def update_project(self, payload: UpdateProjectPayload) -> UpdateProjectResponse:
        raise NotImplementedError
    
    @abstractmethod
    async def delete_project(self, external_id: str, permanently: bool = False) -> bool:
        raise NotImplementedError
    
    #======== Project Milestone Methods ========
    @abstractmethod
    async def create_project_milestone(
        self, 
        payload: CreateProjectMilestonePayload
    ) -> CreateProjectMilestoneResponse:
        """Create a project milestone in the PM service"""
        raise NotImplementedError
    
    @abstractmethod
    async def update_project_milestone(
        self, 
        payload: UpdateProjectMilestonePayload
    ) -> UpdateProjectMilestoneResponse:
        """Update a project milestone in the PM service"""
        raise NotImplementedError
    
    @abstractmethod
    async def delete_project_milestone(self, external_id: str) -> bool:
        """Delete a project milestone from the PM service"""
        raise NotImplementedError
    
    @abstractmethod
    async def create_comment(
        self, 
        payload: CreateCommentPayload
    ) -> CreateCommentResponse:
        """Create a comment in the PM service"""
        raise NotImplementedError
    
    @abstractmethod
    async def update_comment(
        self, 
        payload: UpdateCommentPayload
    ) -> UpdateCommentResponse:
        """Update a comment in the PM service"""
        raise NotImplementedError
    
    @abstractmethod
    async def delete_comment(self, external_id: str) -> bool:
        """Delete a comment from the PM service"""
        raise NotImplementedError