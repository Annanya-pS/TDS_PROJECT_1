"""
src/tds_virtual_ta/llm/prompts.py
FIXED - Correct prompts for STATIC site generation (HTML/CSS/JS only)
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
        attachments_info = "\n\nATTACHMENTS PROVIDED:\n"
        for att in attachments:
            mime_type = att.url.split(";")[0].replace("data:", "") if ":" in att.url else "unknown"
            attachments_info += f"- {att.name} ({mime_type}) - embedded as data URI\n"
        attachments_info += "\nIMPORTANT: Access attachments using their data URIs or embed them inline.\n"
    
    checks_info = ""
    if checks:
        checks_info = "\n\nEVALUATION CRITERIA (MUST MEET ALL):\n"
        for i, check in enumerate(checks, 1):
            checks_info += f"{i}. {check}\n"
        checks_info += "\nCRITICAL: Every check must pass. Ensure all IDs, classes, and functionality exist.\n"
    
    if round == 1 or not existing_code:
        return f'''You are an expert front-end developer specializing in creating modern, responsive static web applications.

TASK:
{brief}
{attachments_info}
{checks_info}

CRITICAL REQUIREMENTS:
1. Create a SINGLE, SELF-CONTAINED HTML file (index.html) with embedded CSS and JavaScript
2. Use ONLY static HTML, CSS, and vanilla JavaScript - NO server-side code
3. Load ALL external libraries from CDN (Bootstrap 5, jQuery, marked, highlight.js, etc.)
4. The page MUST work when opened directly in a browser (file:// protocol)
5. Ensure ALL element IDs mentioned in checks exist and function correctly
6. Use Bootstrap 5.3.0 from jsdelivr CDN for styling
7. Handle errors gracefully with try-catch blocks
8. Make it responsive and professional-looking
9. Add inline comments explaining key functionality

DESIGN GUIDELINES:
- Clean, modern UI with proper spacing
- Use Bootstrap components (cards, forms, buttons, alerts)
- Responsive layout that works on mobile and desktop
- Professional color scheme (avoid harsh colors)
- Loading states and error messages where appropriate

DATA HANDLING:
- For attachments: Use the data URI directly or decode base64 inline
- For CSV/JSON: Parse client-side using JavaScript
- For images: Use img src with data URI or embed inline
- Store temporary data in JavaScript variables (NO localStorage/sessionStorage)

OUTPUT FORMAT (CRITICAL - Follow exactly):

=== index.html ===
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Application Title</title>
    
    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Additional CDN libraries as needed -->
    
    <style>
        /* Custom CSS here */
        body {{
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .card {{
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        /* More custom styles */
    </style>
</head>
<body>
    <div class="container">
        <div class="card p-4 bg-white">
            <h1 class="mb-4">Application Title</h1>
            
            <!-- Your HTML content with ALL required IDs -->
            
        </div>
    </div>
    
    <script>
        // Your JavaScript code here
        // Handle all functionality
        // Meet all evaluation criteria
    </script>
</body>
</html>

=== README.md ===
# Application Title

## Summary
Brief description of what this application does.

## Features
- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Setup
No build steps required. This is a static HTML application.

### Local Usage
1. Download or clone the repository
2. Open `index.html` in any modern web browser
3. The application will run immediately

### GitHub Pages
The application is deployed at: [Your GitHub Pages URL]

## Usage Instructions
1. Step-by-step guide on how to use the application
2. Explain any inputs or interactions
3. Mention expected outputs

## Technical Details

### Technologies Used
- HTML5
- CSS3 (Bootstrap 5.3.0)
- Vanilla JavaScript
- [Any other CDN libraries used]

### Key Features
- Responsive design
- Client-side data processing
- Error handling
- Modern UI/UX

### File Structure
```
.
├── index.html          # Main application file
├── README.md           # This file
└── LICENSE            # MIT License
```

## Code Explanation

### HTML Structure
Explain the main sections and elements.

### CSS Styling
Describe the styling approach and key design decisions.

### JavaScript Functionality
Explain the main functions and data flow:
- Data parsing/processing
- Event handlers
- Calculation logic
- DOM manipulation

## Evaluation Criteria
This application meets the following requirements:
{chr(10).join(f"- {check}" for check in checks)}

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Author
Generated as part of IIT Madras TDS Project

=== LICENSE ===
MIT License

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

CRITICAL NOTES:
1. Generate ONLY these three files marked with === filename ===
2. Ensure index.html is completely self-contained
3. ALL element IDs from checks MUST be present
4. Use proper Bootstrap classes for styling
5. Test all functionality in your mind before outputting
6. NO explanations outside the file markers
7. NO placeholder comments like "// Add code here" - write complete working code
8. Make it production-ready, not a prototype
'''

    else:  # Round 2
        return f'''You are modifying an existing static web application based on new requirements.

MODIFICATION REQUEST:
{brief}
{attachments_info}
{checks_info}

EXISTING CODE:
```html
{existing_code[:3000]}
{"... (truncated for brevity)" if len(existing_code) > 3000 else ""}
```

REQUIREMENTS:
1. PRESERVE all existing functionality that still works
2. ADD the requested new features
3. MODIFY only what's needed to meet the new brief
4. Ensure ALL new element IDs from checks exist
5. Keep the same styling approach (Bootstrap 5)
6. Update README.md to reflect changes
7. Maintain code quality and comments
8. Test compatibility with existing features

OUTPUT FORMAT:
=== index.html ===
[Complete modified HTML with embedded CSS and JS]

=== README.md ===
# Application Title

## Summary
[Updated description including new features]

## Features
[List all features - old and new]

## Changes in Round 2
[Describe what was added/modified]

[Rest of README with updated information]

=== LICENSE ===
[Keep MIT License unchanged]

CRITICAL: Output complete working code, not snippets. Every ID from checks must exist and function.'''


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
SOFTWARE."""