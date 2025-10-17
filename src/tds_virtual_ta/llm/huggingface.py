import httpx
import time
import re
from typing import Dict

from .base import BaseLLMAdapter, LLMGenerationError
from .prompts import create_static_site_prompt, get_mit_license
from ..models import LLMGenerationRequest, LLMGenerationResponse
from ..utils.retry import retry_async
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class HuggingFaceLLMAdapter(BaseLLMAdapter):
    """HuggingFace Inference API adapter - FIXED"""
    
    def __init__(self, api_key: str, model: str, base_url: str):
        super().__init__(api_key, model, base_url)
        self.client = httpx.AsyncClient(timeout=120.0)
        # Construct full URL
        self.endpoint = f"{base_url}/{model}"
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @retry_async(max_attempts=2, exceptions=(httpx.HTTPError,))
    async def generate_application(
        self,
        request: LLMGenerationRequest
    ) -> LLMGenerationResponse:
        """Generate application using HuggingFace Inference API."""
        start_time = time.time()
        
        try:
            prompt = create_static_site_prompt(
                brief=request.brief,
                checks=request.checks,
                attachments=request.attachments,
                round=request.round,
                existing_code=request.existing_code
            )
            
            logger.info(f"Calling HuggingFace API with model {self.model}")
            
            # HuggingFace Inference API format
            response = await self.client.post(
                self.endpoint,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 4000,
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "do_sample": True,
                        "return_full_text": False
                    }
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Parse HF response (can be list or dict)
            content = ""
            if isinstance(data, list) and len(data) > 0:
                content = data[0].get("generated_text", "")
            elif isinstance(data, dict):
                content = data.get("generated_text", "") or data.get("text", "")
            else:
                content = str(data)
            
            if not content:
                raise LLMGenerationError("Empty response from HuggingFace", "HuggingFace", self.model)
            
            # Parse files
            files = self._parse_files_from_response(content)
            
            # Ensure required files
            if "index.html" not in files:
                logger.warning("No index.html found, generating fallback")
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
                additional_files={},
                model_used=self.model,
                generation_time=generation_time
            )
        
        except httpx.HTTPError as e:
            logger.error(f"HuggingFace API error: {e}")
            # If 503, model is loading
            if "503" in str(e):
                raise LLMGenerationError("Model is loading, try again in a minute", "HuggingFace", self.model)
            raise LLMGenerationError(f"API request failed: {str(e)}", "HuggingFace", self.model)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise LLMGenerationError(f"Unexpected error: {str(e)}", "HuggingFace", self.model)
    
    def _parse_files_from_response(self, content: str) -> Dict[str, str]:
        """Parse files from response."""
        files = {}
        
        # Try === filename === format
        pattern = r'===\s*([^\s=]+)\s*===\s*\n(.*?)(?=\n===|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for filename, file_content in matches:
            files[filename.strip()] = file_content.strip()
        
        return files
    
    def _generate_fallback_html(self, brief: str, checks: list) -> str:
        """Generate fallback HTML - same as AIPipe."""
        element_ids = set()
        elements_info = []
        for check in checks:
            ids = re.findall(r'#([\w-]+)', check)
            element_ids.update(ids)
            for elem_id in ids:
                context = check.lower()
                element_type = self._determine_element_type(elem_id, context)
                elements_info.append((elem_id, element_type))
        
        elements_html = ""
        for elem_id, element_type in sorted(elements_info):
            elements_html += self._create_html_element(elem_id, element_type)
    
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic Web Application</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ 
            padding: 2rem; 
            background: #f8f9fa; 
            min-height: 100vh; 
        }}
        .container {{ 
            max-width: 800px; 
        }}
        .card {{ 
            border: none; 
            border-radius: 15px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
        }}
        .form-control:focus, .form-select:focus {{ 
            box-shadow: 0 0 0 0.2rem rgba(0,123,255,0.25); 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card p-4 bg-white">
            <h1 class="h3 mb-4">Web Application</h1>
            <p class="lead mb-4">{brief}</p>
            <div class="dynamic-elements">
{elements_html}
            </div>
        </div>
    </div>
    <script>
        // Generic event handlers
        document.addEventListener('DOMContentLoaded', function() {{
            // Handle button clicks
            document.querySelectorAll('button').forEach(btn => {{
                btn.addEventListener('click', (e) => {{
                    console.log('Button clicked:', e.target.id);
                }});
            }});

            // Handle input changes
            document.querySelectorAll('input, select, textarea').forEach(input => {{
                input.addEventListener('change', (e) => {{
                    console.log('Input changed:', e.target.id, e.target.value);
                }});
            }});
        }});
    </script>
</body>
</html>'''
    
    def _determine_element_type(self, elem_id: str, context: str) -> str:
        """Determine the most appropriate HTML element type based on ID and context."""
        elem_id = elem_id.lower()
        
        # Input types
        if any(word in context for word in ['number', 'calculate', 'sum', 'total']):
            return 'number'
        if any(word in context for word in ['email', 'mail']):
            return 'email'
        if any(word in context for word in ['password', 'pwd']):
            return 'password'
        if any(word in context for word in ['date', 'calendar']):
            return 'date'
        if any(word in context for word in ['color', 'colour']):
            return 'color'
        
        # Other element types
        if any(word in elem_id for word in ['button', 'submit', 'send']):
            return 'button'
        if any(word in elem_id for word in ['select', 'dropdown', 'picker']):
            return 'select'
        if any(word in elem_id for word in ['text', 'area', 'message']):
            return 'textarea'
        if any(word in context for word in ['input']):
            return 'text'
        
        # Default to div for output/display elements
        return 'div'
   
    
    def _create_html_element(self, elem_id: str, element_type: str) -> str:
        """Create HTML element based on type."""
        if element_type == 'button':
            return f'            <button id="{elem_id}" class="btn btn-primary mb-3">{elem_id.replace("-", " ").title()}</button>\n'
        elif element_type == 'select':
            return f'            <select id="{elem_id}" class="form-select mb-3"><option value="">Select an option...</option></select>\n'
        elif element_type == 'textarea':
            return f'            <textarea id="{elem_id}" class="form-control mb-3" rows="3" placeholder="Enter text..."></textarea>\n'
        elif element_type == 'div':
            return f'            <div id="{elem_id}" class="alert alert-light mb-3">Output will appear here</div>\n'
        else:
            # Handle all input types
            return f'            <input type="{element_type}" id="{elem_id}" class="form-control mb-3" placeholder="Enter {element_type}...">\n'


    def _generate_fallback_readme(self, brief: str) -> str:
        """Generate basic README."""
        return f'''# Generated Application

## Description
{brief}

## Usage
Open `index.html` in a web browser.

## License
MIT License
'''
    
    async def check_health(self) -> bool:
        """Check HF API health."""
        try:
            response = await self.client.get(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0
            )
            # 503 means model is loading (still healthy)
            return response.status_code in [200, 503]
        except Exception:
            return False