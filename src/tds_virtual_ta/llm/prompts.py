"""
src/tds_virtual_ta/llm/prompts.py
Prompt templates for static site generation
"""

from typing import List
from ..models import Attachment


def create_static_site_prompt(
    brief: str,
    checks: List[str],
    attachments: List[Attachment],
    round: int = 1,
    existing_code: str = None
) -> str:
    """Create prompt for static HTML/JS/CSS generation."""
    
    attachments_info = ""
    if attachments:
        attachments_info = "\n\nATTACHMENTS:\n"
        for att in attachments:
            mime_type = att.url.split(";")[0].replace("data:", "") if ":" in att.url else "unknown"
            attachments_info += f"- {att.name} ({mime_type})\n"
    
    checks_info = ""
    if checks:
        checks_info = "\n\nEVALUATION CRITERIA:\n"
        for i, check in enumerate(checks, 1):
            checks_info += f"{i}. {check}\n"
    
    if round == 1 or not existing_code:
        return f'''You are an expert Python developer specializing in creating web applications with Gradio and Streamlit.

TASK:
{brief}
{attachments_info}
{checks_info}

REQUIREMENTS:
1. Single HTML file (index.html) with embedded CSS and JavaScript
2. Use vanilla HTML/JS/CSS OR CDN libraries (Bootstrap, jQuery, etc.)
3. NO server-side code - pure static files
4. Handle attachments: embed data URIs or fetch them
5. Professional quality with error handling
6. Meet ALL evaluation criteria
7. Responsive design

OUTPUT FORMAT:

=== index.html ===
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>...</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        /* Your CSS */
    </style>
</head>
<body>
    <!-- Your HTML -->
    <script>
        // Your JavaScript
    </script>
</body>
</html>

=== README.md ===
# Project Title

## Summary
...

## Features
- ...

## Usage
...

## License
MIT

=== LICENSE ===
MIT License
...

Generate complete, working code. No explanations outside file markers.'''

    else:  # Round 2
        return f'''Modify the existing website based on this request.

MODIFICATION REQUEST:
{brief}
{attachments_info}
{checks_info}

EXISTING CODE:
```html
{existing_code}
REQUIREMENTS:

1. Apply requested modifications
2. Preserve existing functionality
3. Meet ALL new evaluation criteria
4. Update README to reflect changes

OUTPUT FORMAT:
=== index.html ===
[Complete modified HTML]
=== README.md ===
[Updated README]
=== LICENSE ===
[Keep MIT License]
Generate complete code.'''
    
def get_mit_license() -> str:
   """Return MIT LICENSE text."""
   return """MIT License
Copyright (c) 2025
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""