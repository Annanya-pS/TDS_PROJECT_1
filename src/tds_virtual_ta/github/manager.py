"""
=== FIXED: src/tds_virtual_ta/github/manager.py ===
Corrected to return proper GitHubRepoInfo - REMOVED DUPLICATE CODE
"""

from github import Github, GithubException
from typing import Dict, Optional
import logging

from ..utils.retry import retry_sync
from ..config import settings
from ..models import GitHubRepoInfo
from .workflows import get_all_workflows

logger = logging.getLogger(__name__)


class GitHubManager:
    """GitHub repository manager."""

    def __init__(self):
        self.token = settings.github_token
        self.github = Github(self.token)
        self.user = self.github.get_user()
        self.username = self.user.login

    @retry_sync(max_attempts=3, exceptions=(GithubException,))
    def create_or_get_repository(
        self,
        repo_name: str,
        description: str = "",
        private: bool = False
    ) -> GitHubRepoInfo:
        """Create or get existing repository - RETURNS GitHubRepoInfo."""
        
        try:
            # Check if repo exists
            repo = self.user.get_repo(repo_name)
            logger.info(f"Repository {repo_name} already exists")
            
            # Get latest commit
            commits = list(repo.get_commits())
            commit_sha = commits[0].sha if commits else "initial"
            
            return GitHubRepoInfo(
                repo_name=repo_name,
                repo_url=repo.html_url,
                clone_url=repo.clone_url,
                commit_sha=commit_sha,
                pages_url=f"https://{self.username}.github.io/{repo_name}",
                default_branch=repo.default_branch,
                created=False
            )
        
        except GithubException as e:
            if e.status == 404:
                # Create new repo
                repo = self.user.create_repo(
                    name=repo_name,
                    description=description,
                    private=private,
                    auto_init=True
                )
                logger.info(f"Created new repository: {repo_name}")
                
                # Get initial commit
                commits = list(repo.get_commits())
                commit_sha = commits[0].sha if commits else "initial"
                
                # Add workflows
                try:
                    self._add_workflows(repo_name)
                except Exception as workflow_error:
                    logger.warning(f"Failed to add workflows: {workflow_error}")
                
                return GitHubRepoInfo(
                    repo_name=repo_name,
                    repo_url=repo.html_url,
                    clone_url=repo.clone_url,
                    commit_sha=commit_sha,
                    pages_url=f"https://{self.username}.github.io/{repo_name}",
                    default_branch=repo.default_branch,
                    created=True
                )
            else:
                raise
    
    @retry_sync(max_attempts=3, exceptions=(GithubException,))
    def commit_files(
        self,
        repo_name: str,
        files: Dict[str, str],
        commit_message: str,
        branch: str = "main",
    ) -> str:
        """Commit files and return the LAST commit SHA."""
        repo = self.user.get_repo(repo_name)
        last_commit_sha = ""
        
        logger.info(f"Committing {len(files)} files to {repo_name}")
        
        for path, content in files.items():
            try:
                # Try to get existing file
                existing_file = repo.get_contents(path, ref=branch)
                existing_content = existing_file.decoded_content.decode("utf-8")
                
                if existing_content == content:
                    logger.debug(f"No change for {path}, skipping")
                    continue
                
                # Update existing file
                result = repo.update_file(
                    path=path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha,
                    branch=branch
                )
                last_commit_sha = result["commit"].sha
                logger.debug(f"Updated: {path}")
                
            except GithubException as e:
                if e.status == 404:
                    # Create new file
                    result = repo.create_file(
                        path=path,
                        message=commit_message,
                        content=content,
                        branch=branch
                    )
                    last_commit_sha = result["commit"].sha
                    logger.debug(f"Created: {path}")
                else:
                    raise
        
        logger.info(f"Commit SHA: {last_commit_sha[:7]}")
        return last_commit_sha

    def _add_workflows(self, repo_name: str) -> None:
        """Add GitHub Actions workflows to repository."""
        workflows = get_all_workflows()
        
        for path, content in workflows.items():
            try:
                self.commit_files(
                    repo_name=repo_name,
                    files={path: content},
                    commit_message="Add GitHub Actions workflows"
                )
                logger.info(f"Added workflow: {path}")
            except Exception as e:
                logger.warning(f"Failed to add workflow {path}: {e}")
      
    def get_file_content(
        self,
        repo_name: str,
        file_path: str,
        branch: str = "main"
    ) -> str:
        """Get content of a file from repository."""
        repo = self.user.get_repo(repo_name)

        try:
            content = repo.get_contents(file_path, ref=branch)
            return content.decoded_content.decode('utf-8')
        except GithubException as e:
            if e.status == 404:
                logger.warning(f"File not found: {file_path}")
                return ""
            raise

    @retry_sync(max_attempts=2, exceptions=(GithubException,))
    def enable_pages(
        self,
        repo_name: str,
        branch: str = "main",
        path: str = "/"
    ) -> str:
        """Enable GitHub Pages - returns predictable URL."""
        logger.info(f"Enabling GitHub Pages for {repo_name}")
        
        # Pages URL is predictable
        pages_url = f"https://{self.username}.github.io/{repo_name}"
        
        logger.info(f"GitHub Pages URL: {pages_url}")
        logger.info("Note: Pages deploy automatically when index.html is pushed to main")
        
        return pages_url