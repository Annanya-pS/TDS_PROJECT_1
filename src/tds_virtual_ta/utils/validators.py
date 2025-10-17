import re
from typing import Optional, List, Tuple
from ..config import settings


def sanitize_repo_name(name: str) -> str:
    """
    Sanitize repository name for GitHub.
    
    Rules:
    - Lowercase alphanumeric with hyphens
    - No leading/trailing hyphens
    - 1-100 characters
    """
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    
    if len(name) < 1:
        raise ValueError("Repository name too short")
    
    if len(name) > settings.max_repo_name_length:
        name = name[:settings.max_repo_name_length].rstrip('-')
    
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$', name):
        raise ValueError(f"Invalid repository name: {name}")
    
    return name


def validate_github_url(url: str) -> Tuple[str, str]:
    """
    Parse GitHub URL to extract owner and repo name.
    
    Returns:
        (owner, repo_name)
    """
    patterns = [
        r'github\.com[:/]([^/]+)/([^/\.]+)',
        r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner, repo = match.groups()
            return owner, repo
    
    raise ValueError(f"Invalid GitHub URL: {url}")


def validate_code_safety(code: str, filename: str = "unknown") -> List[str]:
    """
    Basic code safety validation.
    
    Returns:
        List of warning messages (empty if safe)
    """
    if not settings.enable_code_validation:
        return []
    
    warnings = []
    
    dangerous_patterns = [
        (r'import\s+os\s*;?\s*os\.system', 'Direct os.system() call'),
        (r'subprocess\.(?:call|run|Popen).*shell\s*=\s*True', 'Shell injection risk'),
        (r'eval\s*\(', 'Use of eval()'),
        (r'exec\s*\(', 'Use of exec()'),
        (r'__import__\s*\(', 'Dynamic import'),
        (r'open\s*\([^)]*["\']w["\']', 'File write operation'),
        (r'rm\s+-rf', 'Dangerous shell command'),
        (r'DROP\s+TABLE', 'SQL DROP command'),
    ]
    
    for pattern, description in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            warnings.append(f"{filename}: {description}")
    
    return warnings


def extract_repo_name_from_task(task_spec: str) -> str:
    """
    Extract reasonable repo name from task specification.
    
    Args:
        task_spec: Task description
    
    Returns:
        Sanitized repository name
    """
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', task_spec)
    
    if not words:
        return "generated-app"
    
    name_parts = words[:5]
    name = "-".join(name_parts)
    
    try:
        return sanitize_repo_name(name)
    except ValueError:
        return "generated-app"