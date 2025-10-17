"""
src/tds_virtual_ta/llm/aipipe.py
ENHANCED - Multiple model support with intelligent fallback
"""

import httpx
import time
import re
from typing import Dict, List, Optional

from .base import BaseLLMAdapter, LLMGenerationError
from .prompts import create_static_site_prompt, get_mit_license
from ..models import LLMGenerationRequest, LLMGenerationResponse
from ..utils.retry import retry_async
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class AIPipeLLMAdapter(BaseLLMAdapter):
    """
    AIPipe.org API adapter with multiple model support.
    
    Available models (as of 2025):
    - openai/gpt-4-turbo (best quality, slower)
    - openai/gpt-4o-mini (fast, good quality)
    - anthropic/claude-3-5-sonnet (excellent for code)
    - google/gemini-pro-1.5 (good for long context)
    - meta-llama/llama-3.1-70b-instruct (open source, fast)
    """
    
    # Model priority list (fallback order)
    AVAILABLE_MODELS = [
        "openai/gpt-4-turbo",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-5-sonnet",
        "google/gemini-pro-1.5",
        "meta-llama/llama-3.1-70b-instruct"
    ]
    
    def __init__(self, api_key: str, model: str, base_url: str):
        super().__init__(api_key, model, base_url)
        self.client = httpx.AsyncClient(timeout=120.0)
        
        # Validate model
        if model not in self.AVAILABLE_MODELS:
            logger.warning(f"Model {model} not in known list, will attempt anyway")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def generate_application(
        self,
        request: LLMGenerationRequest
    ) -> LLMGenerationResponse:
        """
        Generate application with intelligent model fallback.
        Tries primary model, then falls back to alternatives.
        """
        start_time = time.time()
        
        # Try models in priority order
        models_to_try = [self.model] + [m for m in self.AVAILABLE_MODELS if m != self.model]
        last_error = None
        
        for model_name in models_to_try[:3]:  # Try max 3 models
            try:
                logger.info(f"Attempting generation with {model_name}")
                result = await self._generate_with_model(request, model_name)
                logger.info(f"✓ Successfully generated with {model_name}")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model_name} failed: {e}")
                continue
        
        # All models failed - use fallback
        logger.error(f"All models failed, using fallback HTML")
        return self._generate_fallback_response(request, start_time)
    
    @retry_async(max_attempts=2, exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def _generate_with_model(
        self,
        request: LLMGenerationRequest,
        model_name: str
    ) -> LLMGenerationResponse:
        """Generate using specific model."""
        start_time = time.time()
        
        prompt = create_static_site_prompt(
            brief=request.brief,
            checks=request.checks,
            attachments=request.attachments,
            round=request.round,
            existing_code=request.existing_code
        )
        
        # AIPipe.org API call
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Parse response
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not content:
            raise LLMGenerationError("Empty response", "AIPipe", model_name)
        
        # Parse files
        files = self._parse_files_from_response(content)
        
        # Ensure required files
        if "index.html" not in files:
            logger.warning("No index.html, generating fallback")
            files["index.html"] = self._generate_fallback_html(request.brief, request.checks)
        if "README.md" not in files:
            files["README.md"] = self._generate_fallback_readme(request.brief)
        if "LICENSE" not in files:
            files["LICENSE"] = get_mit_license()
        
        generation_time = time.time() - start_time
        
        return LLMGenerationResponse(
            index_html=files["index.html"],
            readme_md=files["README.md"],
            license_text=files["LICENSE"],
            additional_files={k: v for k, v in files.items() 
                            if k not in ["index.html", "README.md", "LICENSE"]},
            model_used=model_name,
            generation_time=generation_time
        )
    
    def _parse_files_from_response(self, content: str) -> Dict[str, str]:
        """Parse files from LLM response."""
        files = {}
        
        # Pattern: === filename ===
        pattern = r'===\s*([^\s=]+)\s*===\s*\n(.*?)(?=\n===|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for filename, file_content in matches:
            filename = filename.strip()
            file_content = file_content.strip()
            
            # Remove markdown code blocks
            file_content = re.sub(r'^```\w*\n', '', file_content)
            file_content = re.sub(r'\n```$', '', file_content)
            
            files[filename] = file_content
        
        return files
    
    def _generate_fallback_html(self, brief: str, checks: list) -> str:
        """Generate basic fallback HTML with elements from checks."""
        element_ids = set()
        for check in checks:
            ids = re.findall(r'#([\w-]+)', check)
            element_ids.update(ids)
        
        # Generate HTML for each required element
        elements_html = ""
        for elem_id in sorted(element_ids):
            if 'input' in elem_id or 'num' in elem_id:
                elements_html += f'            <input type="number" id="{elem_id}" class="form-control mb-2" placeholder="{elem_id}">\n'
            elif 'button' in elem_id or 'calculate' in elem_id or 'submit' in elem_id:
                elements_html += f'            <button id="{elem_id}" class="btn btn-primary mb-2">{elem_id.replace("-", " ").title()}</button>\n'
            elif 'select' in elem_id or 'picker' in elem_id or 'filter' in elem_id:
                elements_html += f'            <select id="{elem_id}" class="form-select mb-2">\n                <option value="">Select...</option>\n            </select>\n'
            else:
                elements_html += f'            <div id="{elem_id}" class="mb-2">Result</div>\n'
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Application</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 800px;
        }}
        .card {{
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card p-4 bg-white">
            <h1 class="mb-4">Application</h1>
            <p class="lead">{brief}</p>
            <div class="mt-4">
{elements_html}
            </div>
        </div>
    </div>
    <script>
        console.log('Application loaded');
        
        // Add basic event listeners
        document.querySelectorAll('button').forEach(btn => {{
            btn.addEventListener('click', function() {{
                console.log('Button clicked:', this.id);
            }});
        }});
    </script>
</body>
</html>'''
    
    def _generate_fallback_readme(self, brief: str) -> str:
        """Generate basic README."""
        return f'''# Generated Application

## Summary
{brief}

## Features
- Responsive design with Bootstrap 5
- Clean user interface
- Modern styling

## Setup
No build steps required. This is a static HTML application.

## Usage
1. Open `index.html` in a web browser
2. Or visit the GitHub Pages URL

## Code Explanation
- **index.html**: Main application file with embedded CSS and JavaScript
- Uses Bootstrap 5 from CDN for styling
- Vanilla JavaScript for interactivity

## License
This project is licensed under the MIT License - see the LICENSE file for details.
'''
    
    def _generate_fallback_response(
        self,
        request: LLMGenerationRequest,
        start_time: float
    ) -> LLMGenerationResponse:
        """Generate complete fallback response when all models fail."""
        return LLMGenerationResponse(
            index_html=self._generate_fallback_html(request.brief, request.checks),
            readme_md=self._generate_fallback_readme(request.brief),
            license_text=get_mit_license(),
            additional_files={},
            model_used="fallback",
            generation_time=time.time() - start_time
        )
    
    async def check_health(self) -> bool:
        """Check API health."""
        try:
            response = await self.client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_available_models(self) -> List[str]:
        """List all available models from AIPipe.org"""
        try:
            response = await self.client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
            return self.AVAILABLE_MODELS
        except Exception:
            return self.AVAILABLE_MODELS