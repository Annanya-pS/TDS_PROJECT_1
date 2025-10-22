"""
src/tds_virtual_ta/worker.py
FINAL VERSION - Sanitized repo description
"""

import asyncio
import time
import httpx
import base64
import re
from typing import Dict

from .config import settings
from .models import TaskRequest, EvaluationResult, LLMGenerationRequest
from .llm.aipipe import AIPipeLLMAdapter
from .llm.huggingface import HuggingFaceLLMAdapter
from .llm.base import LLMGenerationError
from .github.manager import GitHubManager
from .utils.logging_config import TaskLogger, get_logger

logger = get_logger(__name__)


def sanitize_description(text: str, max_length: int = 100) -> str:
    """
    Sanitize text for GitHub repo description.
    Remove control characters, newlines, tabs.
    """
    # Replace newlines and tabs with spaces
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Remove other control characters
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Trim and limit length
    text = text.strip()[:max_length]
    return text


async def process_task(request: TaskRequest):
    """Main background task processor - 10 minute timeout."""
    task_logger = TaskLogger(request.task, logger)
    start_time = time.time()
    
    task_logger.info(f"Starting Round {request.round} for {request.email}")
    
    try:
        result = await asyncio.wait_for(
            _process_task_internal(request, task_logger),
            timeout=570  # 9.5 minutes
        )
        
        await post_to_evaluation_url(
            str(request.evaluation_url),
            result,
            task_logger
        )
        
        elapsed = time.time() - start_time
        task_logger.info(f"Task completed in {elapsed:.2f}s")
    
    except asyncio.TimeoutError:
        task_logger.error("Task exceeded 10-minute timeout!")
    except Exception as e:
        task_logger.error(f"Task failed: {e}", exc_info=True)


async def _process_task_internal(
    request: TaskRequest,
    task_logger: TaskLogger
) -> EvaluationResult:
    """Internal processing logic."""
    
    # STEP 1: Parse attachments
    task_logger.info(f"Step 1: Parsing {len(request.attachments)} attachments")
    parsed_attachments = []
    for att in request.attachments:
        parsed_attachments.append({
            "name": att.name,
            "content": _parse_data_uri(att.url),
            "url": att.url
        })
    
    # STEP 2: Get existing code for Round 2
    existing_code = None
    if request.round > 1:
        task_logger.info("Round 2+: Fetching existing code")
        github_manager = GitHubManager()
        try:
            existing_code = github_manager.get_file_content(request.task, "index.html")
        except Exception as e:
            task_logger.warning(f"Could not fetch existing code: {e}")
    
    # STEP 3: Generate app with LLM
    task_logger.info("Step 2: Generating static HTML/JS/CSS app with LLM")
    
    llm_request = LLMGenerationRequest(
        brief=request.brief,
        checks=request.checks,
        attachments=request.attachments,
        round=request.round,
        existing_code=existing_code
    )
    
    llm_response = None
    
    # Try AIPipe first
    try:
        async with AIPipeLLMAdapter(
            settings.aipipe_api_key,
            settings.aipipe_model,
            settings.aipipe_base_url
        ) as adapter:
            llm_response = await adapter.generate_application(llm_request)
            task_logger.info(f"Code generated with {llm_response.model_used}")
    except LLMGenerationError as e:
        task_logger.warning(f"AIPipe failed: {e}, trying HuggingFace fallback")
        
        try:
            async with HuggingFaceLLMAdapter(
                settings.hf_token,
                settings.hf_inference_model,
                settings.hf_inference_url
            ) as adapter:
                llm_response = await adapter.generate_application(llm_request)
                task_logger.info(f"Code generated with fallback: {llm_response.model_used}")
        except Exception as fallback_error:
            raise Exception(f"Both LLM providers failed: {fallback_error}")
    
    if not llm_response:
        raise Exception("Failed to generate code")
    
    # STEP 4: Create/update GitHub repo
    task_logger.info("Step 3: Managing GitHub repository")
    
    # IMPORTANT: Use task ID as repo name (per specs)
    repo_name = request.task  # e.g., "captcha-solver-a1b2c"
    
    # ✅ FIX: Sanitize description to remove control characters
    safe_description = sanitize_description(
        f"TDS Project Round {request.round}: {request.brief}"
    )
    
    github_manager = GitHubManager()
    
    repo_info = github_manager.create_or_get_repository(
        repo_name=repo_name,
        description=safe_description,  # ✅ Now sanitized
        private=False  # Must be public
    )
    
    task_logger.info(f"Repository: {repo_info.repo_url}")
    
    # STEP 5: Prepare files
    files = {
        "index.html": llm_response.index_html,
        "README.md": llm_response.readme_md,
        "LICENSE": llm_response.license_text,
    }
    
    # Add additional files
    files.update(llm_response.additional_files)
    
    # Add attachments if needed
    for att in parsed_attachments:
        if att["name"] not in files and att["content"]:
            files[att["name"]] = att["content"]
    
    task_logger.info(f"Committing {len(files)} files")
    
    # STEP 6: Commit files
    commit_sha = github_manager.commit_files(
        repo_name=repo_info.repo_name,
        files=files,
        commit_message=f"Round {request.round}: {request.brief[:50]}"
    )
    
    task_logger.info(f"Committed: {commit_sha[:7]}")
    
    # STEP 7: Enable GitHub Pages
    task_logger.info("Step 4: Enabling GitHub Pages")
    
    pages_url = github_manager.enable_pages(repo_info.repo_name)
    
    task_logger.info(f"GitHub Pages: {pages_url}")
    
    # STEP 8: Return result
    result = EvaluationResult(
        email=request.email,
        task=request.task,
        round=request.round,
        nonce=request.nonce,
        repo_url=repo_info.repo_url,
        commit_sha=commit_sha,
        pages_url=pages_url
    )
    
    return result


async def post_to_evaluation_url(
    evaluation_url: str,
    result: EvaluationResult,
    task_logger: TaskLogger,
    max_retries: int = 5
):
    """
    POST result with exponential backoff: 1, 2, 4, 8, 16 seconds.
    Spec-compliant retry timing.
    """
    
    task_logger.info(f"Posting result to: {evaluation_url}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    evaluation_url,
                    json=result.model_dump(mode='json'),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    task_logger.info("✓ Result posted successfully (HTTP 200)")
                    return True
                else:
                    task_logger.warning(
                        f"Evaluation URL returned {response.status_code}: {response.text[:100]}"
                    )
            except Exception as e:
                task_logger.error(f"POST attempt {attempt + 1} failed: {e}")
            
            # Exponential backoff: 1, 2, 4, 8, 16 seconds
            if attempt < max_retries - 1:
                delay = 2 ** attempt
                task_logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
    
    task_logger.error("Failed to POST result after all retries")
    return False


def _parse_data_uri(data_uri: str) -> str:
    """Parse data URI to extract content."""

    if not data_uri or not isinstance(data_uri, str):
        return ""
    if not data_uri.startswith("data:"):
        return data_uri
    
    try:
        # Format: data:mime/type;base64,encoded_data
        header, encoded = data_uri.split(",", 1)
        
        if "base64" in header:
            decoded = base64.b64decode(encoded)
            try:
                return decoded.decode('utf-8')
            except UnicodeDecodeError:
                # Binary data - return as hex or save as file
                return decoded.hex()
        else:
            # URL-encoded
            from urllib.parse import unquote
            return unquote(encoded)
    except (ValueError, TypeError, base64.binascii.Error) as e:
        logger.error(f"Failed to parse data URI: {e}")
        return ""
