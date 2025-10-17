
from abc import ABC, abstractmethod
from typing import Optional, Dict
from ..models import LLMGenerationRequest, LLMGenerationResponse


class BaseLLMAdapter(ABC):
    """Abstract base class for LLM adapters."""
    
    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        """Initialize LLM adapter."""
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    @abstractmethod
    async def generate_application(
        self,
        request: LLMGenerationRequest
    ) -> LLMGenerationResponse:
        """
        Generate complete application code.
        
        Must generate:
        - index.html
        - README.md
        - LICENSE
        - Any additional static assets
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Check if LLM service is available."""
        pass
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for static site generation."""
        return """You are an expert web developer specializing in creating static websites. 
        Your task is to generate production-ready static sites based on user requirements.

Your task is to generate production-ready code based on user requirements. You must:

1. Write clean, well-documented Python code
2. Include all necessary dependencies in requirements.txt
3. Create a working Dockerfile for deployment
4. Follow best practices for security and performance
5. Make the application user-friendly and robust

IMPORTANT: Generate ONLY the requested files. Do not include explanations or markdown formatting outside of code comments."""


class LLMGenerationError(Exception):
    """Exception raised when LLM generation fails."""
    
    def __init__(self, message: str, provider: str, model: str):
        self.message = message
        self.provider = provider
        self.model = model
        super().__init__(f"[{provider}/{model}] {message}")

