"""GitHub pull request creation and management."""

from typing import Optional, List
from github import Github, GithubException
from pathlib import Path
import subprocess
from datetime import datetime

from src.config import settings
from src.models.schemas import GeneratedFix, Diagnosis, PullRequest, PRStatus
from src.ai.llm_client import LLMClient


class PRCreator:
    """Creates and manages GitHub pull requests for fixes."""

    def __init__(
        self,
        github_token: Optional[str] = None,
        repo_name: Optional[str] = None,
    ) -> None:
        """
        Initialize the PR creator.

        Args:
            github_token: GitHub personal access token (uses config if not provided)
            repo_name: Repository name in format "owner/repo" (uses config if not provided)
        """
        self.github_token = github_token or settings.github_token
        self.repo_name = repo_name or settings.github_repo

        if not self.github_token:
            raise ValueError("GitHub token not provided")
        if not self.repo_name:
            raise ValueError("Repository name not provided")

        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)
        self.llm_client = LLMClient()

    def create_pr(
        self,
        diagnosis: Diagnosis,
        fix: GeneratedFix,
        codebase_path: str,
        base_branch: Optional[str] = None,
    ) -> PullRequest:
        """
        Create a pull request with the generated fix.

        Args:
            diagnosis: Issue diagnosis
            fix: Generated fix
            codebase_path: Path to local codebase
            base_branch: Base branch for PR (default from config)

        Returns:
            PullRequest object with PR details
        """
        base_branch = base_branch or settings.github_default_branch
        branch_name = self._create_branch_name(diagnosis)

        try:
            # Create and checkout new branch
            self._create_branch(codebase_path, branch_name, base_branch)

            # Apply changes
            self._apply_changes(codebase_path, fix)

            # Commit changes
            self._commit_changes(codebase_path, fix)

            # Push branch
            self._push_branch(codebase_path, branch_name)

            # Create PR description
            pr_content = self.llm_client.create_pr_description(diagnosis, fix)

            # Create GitHub PR
            github_pr = self.repo.create_pull(
                title=pr_content["title"],
                body=pr_content["body"],
                head=branch_name,
                base=base_branch,
            )

            # Add labels
            self._add_labels(github_pr, diagnosis)

            return PullRequest(
                pr_id=str(github_pr.id),
                fix_id=fix.fix_id,
                branch_name=branch_name,
                pr_number=github_pr.number,
                pr_url=github_pr.html_url,
                title=pr_content["title"],
                body=pr_content["body"],
                status=PRStatus.CREATED,
            )

        except Exception as e:
            return PullRequest(
                pr_id=f"failed_{datetime.utcnow().isoformat()}",
                fix_id=fix.fix_id,
                branch_name=branch_name,
                title=fix.title,
                body=str(e),
                status=PRStatus.FAILED,
            )

    def update_pr(
        self, pr: PullRequest, fix: GeneratedFix, codebase_path: str
    ) -> PullRequest:
        """
        Update an existing PR with new changes.

        Args:
            pr: Existing PR to update
            fix: Updated fix
            codebase_path: Path to local codebase

        Returns:
            Updated PullRequest object
        """
        try:
            # Checkout branch
            self._checkout_branch(codebase_path, pr.branch_name)

            # Apply changes
            self._apply_changes(codebase_path, fix)

            # Commit changes
            self._commit_changes(codebase_path, fix, amend=True)

            # Force push
            self._push_branch(codebase_path, pr.branch_name, force=True)

            pr.status = PRStatus.UPDATED
            return pr

        except Exception as e:
            print(f"Error updating PR: {e}")
            pr.status = PRStatus.FAILED
            return pr

    def merge_pr(self, pr_number: int, merge_method: str = "squash") -> bool:
        """
        Merge a pull request.

        Args:
            pr_number: PR number to merge
            merge_method: Merge method ("merge", "squash", or "rebase")

        Returns:
            True if successful
        """
        try:
            github_pr = self.repo.get_pull(pr_number)
            github_pr.merge(merge_method=merge_method)
            return True
        except GithubException as e:
            print(f"Error merging PR: {e}")
            return False

    def close_pr(self, pr_number: int) -> bool:
        """
        Close a pull request without merging.

        Args:
            pr_number: PR number to close

        Returns:
            True if successful
        """
        try:
            github_pr = self.repo.get_pull(pr_number)
            github_pr.edit(state="closed")
            return True
        except GithubException as e:
            print(f"Error closing PR: {e}")
            return False

    def add_comment(self, pr_number: int, comment: str) -> bool:
        """
        Add a comment to a PR.

        Args:
            pr_number: PR number
            comment: Comment text

        Returns:
            True if successful
        """
        try:
            github_pr = self.repo.get_pull(pr_number)
            github_pr.create_issue_comment(comment)
            return True
        except GithubException as e:
            print(f"Error adding comment: {e}")
            return False

    def get_pr_status(self, pr_number: int) -> dict:
        """
        Get status of a PR including checks.

        Args:
            pr_number: PR number

        Returns:
            Dictionary with PR status
        """
        try:
            github_pr = self.repo.get_pull(pr_number)
            commits = list(github_pr.get_commits())
            latest_commit = commits[-1] if commits else None

            checks = []
            if latest_commit:
                check_runs = latest_commit.get_check_runs()
                checks = [
                    {
                        "name": check.name,
                        "status": check.status,
                        "conclusion": check.conclusion,
                    }
                    for check in check_runs
                ]

            return {
                "state": github_pr.state,
                "merged": github_pr.merged,
                "mergeable": github_pr.mergeable,
                "checks": checks,
                "reviews": [
                    {"user": review.user.login, "state": review.state}
                    for review in github_pr.get_reviews()
                ],
            }

        except GithubException as e:
            print(f"Error getting PR status: {e}")
            return {"error": str(e)}

    def _create_branch_name(self, diagnosis: Diagnosis) -> str:
        """Create a branch name from diagnosis."""
        # Sanitize summary for branch name
        summary = diagnosis.summary.lower()
        summary = "".join(c if c.isalnum() or c in " -" else "" for c in summary)
        summary = summary.replace(" ", "-")[:50]

        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        return f"auto-fix/{summary}-{timestamp}"

    def _create_branch(self, codebase_path: str, branch_name: str, base_branch: str) -> None:
        """Create a new git branch."""
        commands = [
            f"git fetch origin {base_branch}",
            f"git checkout -b {branch_name} origin/{base_branch}",
        ]
        for cmd in commands:
            subprocess.run(cmd, shell=True, cwd=codebase_path, check=True)

    def _checkout_branch(self, codebase_path: str, branch_name: str) -> None:
        """Checkout an existing branch."""
        subprocess.run(
            f"git checkout {branch_name}",
            shell=True,
            cwd=codebase_path,
            check=True,
        )

    def _apply_changes(self, codebase_path: str, fix: GeneratedFix) -> None:
        """Apply file changes from fix."""
        codebase = Path(codebase_path)
        for file_path, content in fix.file_changes.items():
            full_path = codebase / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

    def _commit_changes(
        self, codebase_path: str, fix: GeneratedFix, amend: bool = False
    ) -> None:
        """Commit changes to git."""
        # Add all changes
        subprocess.run("git add -A", shell=True, cwd=codebase_path, check=True)

        # Create commit message
        commit_msg = f"""{fix.title}

{fix.description}

Auto-generated fix by Plant AI System Analyzer
Fix ID: {fix.fix_id}
"""

        # Commit
        amend_flag = "--amend --no-edit" if amend else ""
        subprocess.run(
            f'git commit {amend_flag} -m "{commit_msg}"',
            shell=True,
            cwd=codebase_path,
            check=True,
        )

    def _push_branch(
        self, codebase_path: str, branch_name: str, force: bool = False
    ) -> None:
        """Push branch to remote."""
        force_flag = "--force" if force else ""
        subprocess.run(
            f"git push {force_flag} origin {branch_name}",
            shell=True,
            cwd=codebase_path,
            check=True,
        )

    def _add_labels(self, github_pr, diagnosis: Diagnosis) -> None:
        """Add labels to PR based on diagnosis."""
        labels = []

        # Severity label
        labels.append(f"severity:{diagnosis.severity.value}")

        # Category label
        labels.append(f"category:{diagnosis.category.value}")

        # Auto-fix label
        labels.append("auto-generated")

        try:
            # Create labels if they don't exist
            existing_labels = {label.name for label in self.repo.get_labels()}
            for label_name in labels:
                if label_name not in existing_labels:
                    self._create_label(label_name)

            # Add labels to PR
            github_pr.add_to_labels(*labels)
        except GithubException as e:
            print(f"Error adding labels: {e}")

    def _create_label(self, label_name: str) -> None:
        """Create a label in the repository."""
        # Color mapping
        colors = {
            "severity:critical": "d73a4a",
            "severity:high": "ff6b6b",
            "severity:medium": "fbca04",
            "severity:low": "0e8a16",
            "category:performance": "1d76db",
            "category:security": "d93f0b",
            "category:reliability": "5319e7",
            "auto-generated": "bfdadc",
        }

        color = colors.get(label_name, "ededed")

        try:
            self.repo.create_label(name=label_name, color=color)
        except GithubException:
            pass  # Label might already exist
