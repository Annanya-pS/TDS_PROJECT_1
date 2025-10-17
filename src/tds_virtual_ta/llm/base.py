
"""
src/tds_virtual_ta/llm/base.py
FIXED - Correct system prompt for static sites
"""

from abc import ABC, abstractmethod
from typing import Optional
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
        Generate complete static web application.
        
        Must generate:
        - index.html (self-contained with embedded CSS/JS)
        - README.md
        - LICENSE
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Check if LLM service is available."""
        pass
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for static site generation."""
        return """You are an expert front-end web developer specializing in creating production-ready static web applications using HTML, CSS, and JavaScript.

Your expertise includes:
- Writing clean, semantic HTML5
- Modern CSS3 with responsive design
- Vanilla JavaScript for interactivity
- Using CDN libraries (Bootstrap, jQuery, marked, highlight.js, etc.)
- Client-side data processing (CSV, JSON, images)
- Accessibility and cross-browser compatibility
- Professional UI/UX design principles

CRITICAL RULES:
1. Generate ONLY static files - NO server-side code
2. Create self-contained HTML with embedded CSS and JavaScript
3. Use CDN for all external libraries (Bootstrap 5, etc.)
4. Ensure code works when opened directly in a browser
5. Meet ALL specified evaluation criteria
6. Include proper error handling
7. Write clean, commented, production-ready code
8. Make responsive, professional-looking interfaces

OUTPUT: Only the requested files with === filename === markers. No explanations outside code."""


class LLMGenerationError(Exception):
    """Exception raised when LLM generation fails."""
    
    def __init__(self, message: str, provider: str, model: str):
        self.message = message
        self.provider = provider
        self.model = model
        super().__init__(f"[{provider}/{model}] {message}")
