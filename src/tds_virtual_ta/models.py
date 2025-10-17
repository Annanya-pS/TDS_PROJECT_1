"""
=== CORRECTED: src/tds_virtual_ta/models.py ===
Based on official project specifications
"""

from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, EmailStr, field_validator


class Attachment(BaseModel):
    """Attachment with data URI."""
    name: str
    url: str  # data URI like "data:image/png;base64,..."


class TaskRequest(BaseModel):
    """
    CORRECTED: Actual request format from IITM TDS Server.
    
    This matches the official specification exactly.
    """
    email: EmailStr = Field(..., description="Student email ID")
    secret: str = Field(..., description="Student-provided secret")
    task: str = Field(..., description="Unique task ID like 'captcha-solver-...'")
    round: int = Field(..., ge=1, le=3, description="Round number (1, 2, or 3)")
    nonce: str = Field(..., description="Unique nonce to pass back")
    brief: str = Field(..., description="What the app needs to do")
    checks: List[str] = Field(default_factory=list, description="Evaluation criteria")
    evaluation_url: HttpUrl = Field(..., description="URL to POST results to")
    attachments: List[Attachment] = Field(default_factory=list, description="Attached files as data URIs")


class TaskResponse(BaseModel):
    """
    Immediate HTTP 200 response to task submission.
    
    Can be simple acknowledgment - specs don't define exact format.
    """
    status: str = Field(default="accepted")
    message: str = Field(default="Request received, processing")


class EvaluationResult(BaseModel):
    """
    CORRECTED: Result to POST to evaluation_url.
    
    This must be sent within 10 minutes of receiving request.
    """
    email: EmailStr = Field(..., description="Copy from request")
    task: str = Field(..., description="Copy from request")
    round: int = Field(..., description="Copy from request")
    nonce: str = Field(..., description="Copy from request")
    repo_url: str = Field(..., description="GitHub repo URL")
    commit_sha: str = Field(..., description="Latest commit SHA")
    pages_url: str = Field(..., description="GitHub Pages URL")


class LLMGenerationRequest(BaseModel):
    """Internal model for LLM requests."""
    brief: str
    checks: List[str]
    attachments: List[Attachment]
    round: int = 1
    existing_code: Optional[str] = None

class LLMGenerationResponse(BaseModel):
    """Internal model for LLM responses."""
    model_config = {"protected_namespaces": ()}
    index_html: str
    readme_md: str
    license_text: str
    additional_files: Dict[str, str] = Field(default_factory=dict)
    model_used: str
    generation_time: float


class GitHubRepoInfo(BaseModel):
    """Info about created/updated repo."""
    repo_name: str
    repo_url: str
    clone_url: str
    commit_sha: str
    pages_url: str
    default_branch: str = "main"
    created: bool = False