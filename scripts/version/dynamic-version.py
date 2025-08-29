#!/usr/bin/env python3
"""
Dynamic Version Management System
Automatically determines version based on Git history and semantic versioning rules
"""

import os
import re
import subprocess
import json
import argparse
from typing import Dict, Optional, Tuple
from datetime import datetime


class DynamicVersionManager:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.version_file = os.path.join(repo_path, "VERSION")
        self.current_version = self._read_current_version()

    def _read_current_version(self) -> str:
        """Read current version from VERSION file"""
        try:
            with open(self.version_file, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "0.1.0"

    def _write_version(self, version: str) -> None:
        """Write version to VERSION file"""
        with open(self.version_file, "w") as f:
            f.write(version)

    def _run_git_command(self, command: str) -> Optional[str]:
        """Run git command and return output"""
        try:
            result = subprocess.run(
                command.split(),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _get_last_tag(self) -> Optional[str]:
        """Get the last git tag"""
        return self._run_git_command("git describe --tags --abbrev=0")

    def _get_commits_since_last_tag(self) -> list:
        """Get commit messages since last tag"""
        last_tag = self._get_last_tag()
        if last_tag:
            command = f"git log {last_tag}..HEAD --oneline"
        else:
            command = "git log --oneline"

        output = self._run_git_command(command)
        if not output:
            return []

        return output.split("\n")

    def _analyze_commit_messages(self, commits: list) -> Dict[str, int]:
        """Analyze commit messages to determine version bump type"""
        patterns = {
            "breaking": [
                r"BREAKING CHANGE",
                r"!:",
                r"feat!:",
                r"fix!:",
                r"refactor!:",
                r"perf!:",
            ],
            "feature": [r"^feat:", r"^feat\(", r"add ", r"implement ", r"feature:"],
            "fix": [r"^fix:", r"^fix\(", r"bug", r"hotfix", r"patch", r"security"],
            "chore": [
                r"^chore:",
                r"^docs:",
                r"^style:",
                r"^test:",
                r"^ci:",
                r"^build:",
            ],
        }

        counts = {"breaking": 0, "feature": 0, "fix": 0, "chore": 0}

        for commit in commits:
            commit_lower = commit.lower()
            for change_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, commit_lower):
                        counts[change_type] += 1
                        break

        return counts

    def _determine_version_bump(self, change_counts: Dict[str, int]) -> str:
        """Determine version bump type based on change counts"""
        if change_counts["breaking"] > 0:
            return "major"
        elif change_counts["feature"] > 0:
            return "minor"
        elif change_counts["fix"] > 0:
            return "patch"
        else:
            return "patch"  # Default for chores and other changes

    def _increment_version(self, version: str, bump_type: str) -> str:
        """Increment version based on semantic versioning"""
        try:
            major, minor, patch = map(int, version.split("."))
        except ValueError:
            major, minor, patch = 0, 1, 0

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1

        return f"{major}.{minor}.{patch}"

    def _get_git_metadata(self) -> Dict:
        """Get additional git metadata for version"""
        metadata = {}

        # Get current commit hash
        commit_hash = self._run_git_command("git rev-parse --short HEAD")
        if commit_hash:
            metadata["commit"] = commit_hash

        # Get current branch
        branch = self._run_git_command("git rev-parse --abbrev-ref HEAD")
        if branch:
            metadata["branch"] = branch

        # Get commit count
        commit_count = self._run_git_command("git rev-list --count HEAD")
        if commit_count:
            metadata["build"] = commit_count

        # Get last commit timestamp
        timestamp = self._run_git_command("git log -1 --format=%ct")
        if timestamp:
            metadata["timestamp"] = datetime.fromtimestamp(int(timestamp)).isoformat()

        return metadata

    def calculate_next_version(self) -> Tuple[str, Dict]:
        """Calculate the next version based on git history"""
        commits = self._get_commits_since_last_tag()
        if not commits:
            # No new commits, return current version
            metadata = self._get_git_metadata()
            return self.current_version, metadata

        change_counts = self._analyze_commit_messages(commits)
        bump_type = self._determine_version_bump(change_counts)
        next_version = self._increment_version(self.current_version, bump_type)

        metadata = self._get_git_metadata()
        metadata.update(
            {
                "previous_version": self.current_version,
                "bump_type": bump_type,
                "changes": change_counts,
                "commit_count": len(commits),
            }
        )

        return next_version, metadata

    def update_version(self, dry_run: bool = False) -> Tuple[str, Dict]:
        """Update version and return new version with metadata"""
        next_version, metadata = self.calculate_next_version()

        if not dry_run and next_version != self.current_version:
            self._write_version(next_version)
            self.current_version = next_version

        return next_version, metadata

    def create_version_info_json(self, output_path: str = None) -> str:
        """Create version info JSON file"""
        if output_path is None:
            output_path = os.path.join(self.repo_path, "version-info.json")

        version, metadata = self.calculate_next_version()

        version_info = {
            "version": version,
            "build_time": datetime.now().isoformat(),
            "git": metadata,
        }

        with open(output_path, "w") as f:
            json.dump(version_info, f, indent=2)

        return output_path


def main():
    parser = argparse.ArgumentParser(description="Dynamic Version Management")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--get-version", action="store_true", help="Get current/next version"
    )
    parser.add_argument(
        "--update", action="store_true", help="Update version based on git history"
    )
    parser.add_argument(
        "--create-info", action="store_true", help="Create version-info.json file"
    )
    parser.add_argument("--repo-path", default=".", help="Repository path")
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args()

    manager = DynamicVersionManager(args.repo_path)

    if args.get_version:
        version, metadata = manager.calculate_next_version()
        if args.output_format == "json":
            print(json.dumps({"version": version, "metadata": metadata}, indent=2))
        else:
            print(f"Current version: {manager.current_version}")
            print(f"Next version: {version}")
            if metadata.get("bump_type"):
                print(f"Bump type: {metadata['bump_type']}")
                print(f"Changes: {metadata['changes']}")

    elif args.update:
        version, metadata = manager.update_version(args.dry_run)
        if args.output_format == "json":
            print(json.dumps({"version": version, "metadata": metadata}, indent=2))
        else:
            action = "Would update" if args.dry_run else "Updated"
            print(f"{action} version to: {version}")
            if metadata.get("bump_type"):
                print(f"Bump type: {metadata['bump_type']}")

    elif args.create_info:
        info_file = manager.create_version_info_json()
        print(f"Created version info: {info_file}")

    else:
        version, metadata = manager.calculate_next_version()
        print(f"Current version: {manager.current_version}")
        print(f"Next version: {version}")
        print(f"Use --update to apply changes")


if __name__ == "__main__":
    main()
