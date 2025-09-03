"""
Base models for Financial Analytics Platform
Common base classes and response models
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

# Generic type for pagination
T = TypeVar('T')


class BaseModel(BaseModel):
    """Base model with common configuration"""
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
    )


class BaseResponse(BaseModel):
    """Base response model"""
    
    success: bool = Field(default=True, description="Operation success status")
    message: Optional[str] = Field(default=None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response model"""
    
    data: List[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Page size")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class ErrorResponse(BaseResponse):
    """Error response model"""
    
    success: bool = Field(default=False, description="Operation success status")
    error_code: Optional[str] = Field(default=None, description="Error code")
    error_details: Optional[Any] = Field(default=None, description="Error details")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")


class HealthCheckResponse(BaseResponse):
    """Health check response model"""
    
    status: str = Field(description="Service status")
    version: str = Field(description="Service version")
    uptime: float = Field(description="Service uptime in seconds")
    checks: dict = Field(description="Health check results")


class AuditLogEntry(BaseModel):
    """Audit log entry model"""
    
    id: UUID = Field(description="Audit log entry ID")
    org_id: Optional[UUID] = Field(default=None, description="Organization ID")
    user_id: Optional[UUID] = Field(default=None, description="User ID")
    action: str = Field(description="Action performed")
    resource_type: Optional[str] = Field(default=None, description="Resource type")
    resource_id: Optional[UUID] = Field(default=None, description="Resource ID")
    details: dict = Field(default_factory=dict, description="Action details")
    ip_address: Optional[str] = Field(default=None, description="IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    created_at: datetime = Field(description="Timestamp of action")


class MetadataModel(BaseModel):
    """Model with metadata support"""
    
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class SoftDeleteModel(MetadataModel):
    """Model with soft delete support"""
    
    is_active: bool = Field(default=True, description="Whether the record is active")
    deleted_at: Optional[datetime] = Field(default=None, description="Soft delete timestamp")


class TimestampedModel(BaseModel):
    """Model with timestamp fields"""
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class IDModel(BaseModel):
    """Model with ID field"""
    
    id: UUID = Field(description="Unique identifier")


class OrganizationScopedModel(IDModel):
    """Model scoped to an organization"""
    
    org_id: UUID = Field(description="Organization ID")


class UserScopedModel(OrganizationScopedModel):
    """Model scoped to a user within an organization"""
    
    user_id: UUID = Field(description="User ID")


class SearchFilters(BaseModel):
    """Base search filters model"""
    
    query: Optional[str] = Field(default=None, description="Search query")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


class DateRangeFilters(SearchFilters):
    """Search filters with date range"""
    
    start_date: Optional[str] = Field(default=None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(default=None, description="End date (ISO format)")
    date_field: str = Field(default="created_at", description="Date field to filter on")


class ExportOptions(BaseModel):
    """Export options model"""
    
    format: str = Field(default="json", description="Export format")
    include_metadata: bool = Field(default=True, description="Include metadata in export")
    compression: Optional[str] = Field(default=None, description="Compression format")
    filename: Optional[str] = Field(default=None, description="Export filename")