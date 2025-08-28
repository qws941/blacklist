#!/usr/bin/env python3
"""
Container Error Monitor and GitHub Issue Auto-creator
Monitors Docker container logs for errors and automatically creates GitHub issues
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import requests


class ContainerErrorMonitor:
    """Monitor Docker containers and create GitHub issues for errors"""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_repo = os.getenv("GITHUB_REPO", "qws941/blacklist")
        self.monitor_interval = int(os.getenv("MONITOR_INTERVAL", "60"))  # seconds
        self.error_threshold = int(
            os.getenv("ERROR_THRESHOLD", "5")
        )  # errors before issue
        self.containers = os.getenv(
            "MONITOR_CONTAINERS", "blacklist-app,blacklist-postgres,blacklist-redis"
        ).split(",")

        # Error patterns to monitor
        self.error_patterns = [
            r"ERROR",
            r"FATAL",
            r"CRITICAL",
            r"Exception",
            r"Traceback",
            r"Failed",
            r"Error:",
            r"panic:",
            r"relation .* does not exist",
            r"connection refused",
            r"timeout",
            r"permission denied",
            r"out of memory",
            r"disk full",
            r"Authentication failed",
        ]

        # Track errors to avoid duplicate issues
        self.seen_errors: Dict[str, Set[str]] = {}
        self.error_counts: Dict[str, int] = {}
        self.last_issue_time: Dict[str, datetime] = {}

    def get_container_logs(self, container_name: str, since: str = "1m") -> List[str]:
        """Get container logs since specified time"""
        try:
            cmd = f"docker logs {container_name} --since {since} 2>&1"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                print(f"⚠️ Failed to get logs for {container_name}: {result.stderr}")
                return []

            return result.stdout.strip().split("\n") if result.stdout else []

        except subprocess.TimeoutExpired:
            print(f"⏱️ Timeout getting logs for {container_name}")
            return []
        except Exception as e:
            print(f"❌ Error getting logs for {container_name}: {e}")
            return []

    def extract_errors(self, logs: List[str], container_name: str) -> List[Dict]:
        """Extract error messages from logs"""
        errors = []

        for line in logs:
            for pattern in self.error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Get context (2 lines before and after)
                    context_start = max(0, logs.index(line) - 2)
                    context_end = min(len(logs), logs.index(line) + 3)
                    context = logs[context_start:context_end]

                    error_hash = self.get_error_hash(line)

                    # Check if we've seen this error before
                    if container_name not in self.seen_errors:
                        self.seen_errors[container_name] = set()

                    if error_hash not in self.seen_errors[container_name]:
                        errors.append(
                            {
                                "container": container_name,
                                "timestamp": datetime.now().isoformat(),
                                "error_line": line,
                                "context": context,
                                "pattern": pattern,
                                "hash": error_hash,
                            }
                        )
                        self.seen_errors[container_name].add(error_hash)

                    break  # Don't match multiple patterns for same line

        return errors

    def get_error_hash(self, error_line: str) -> str:
        """Generate a hash for error deduplication"""
        # Remove timestamps, IDs, and specific values
        cleaned = re.sub(r"\d{4}-\d{2}-\d{2}", "DATE", error_line)
        cleaned = re.sub(r"\d{2}:\d{2}:\d{2}", "TIME", cleaned)
        cleaned = re.sub(r"\b\d+\b", "NUM", cleaned)
        cleaned = re.sub(r"0x[0-9a-fA-F]+", "HEX", cleaned)
        return hash(cleaned)

    def get_container_health(self, container_name: str) -> Dict:
        """Get container health status"""
        try:
            cmd = f"docker inspect {container_name} --format '{{{{json .State}}}}'"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0 and result.stdout:
                state = json.loads(result.stdout)
                return {
                    "status": state.get("Status", "unknown"),
                    "running": state.get("Running", False),
                    "health": state.get("Health", {}).get("Status", "unknown")
                    if "Health" in state
                    else "no healthcheck",
                    "exit_code": state.get("ExitCode", 0),
                    "started_at": state.get("StartedAt", ""),
                    "finished_at": state.get("FinishedAt", ""),
                }
        except Exception as e:
            print(f"❌ Error getting health for {container_name}: {e}")

        return {"status": "unknown", "running": False, "health": "unknown"}

    def create_github_issue(self, errors: List[Dict], container_name: str) -> bool:
        """Create GitHub issue for container errors"""
        if not self.github_token:
            print("⚠️ GitHub token not configured, skipping issue creation")
            return False

        # Check rate limiting (max 1 issue per container per hour)
        if container_name in self.last_issue_time:
            if datetime.now() - self.last_issue_time[container_name] < timedelta(
                hours=1
            ):
                print(f"⏳ Rate limiting: Issue for {container_name} created recently")
                return False

        # Get container health status
        health = self.get_container_health(container_name)

        # Prepare issue content
        title = f"🐛 [Auto] Container Error: {container_name}"

        # Group errors by pattern
        error_groups = {}
        for error in errors:
            pattern = error["pattern"]
            if pattern not in error_groups:
                error_groups[pattern] = []
            error_groups[pattern].append(error)

        body = f"""## 🚨 Automatic Error Detection

Container `{container_name}` has encountered {len(errors)} error(s) in the last monitoring period.

### 📊 Container Status
- **Status**: {health['status']}
- **Running**: {'✅ Yes' if health['running'] else '❌ No'}
- **Health Check**: {health['health']}
- **Exit Code**: {health.get('exit_code', 0)}

### 🔍 Error Summary
"""

        for pattern, group_errors in error_groups.items():
            body += f"\n#### Pattern: `{pattern}` ({len(group_errors)} occurrence(s))\n"

            for i, error in enumerate(
                group_errors[:3], 1
            ):  # Show max 3 examples per pattern
                body += f"\n**Example {i}:**\n```\n"
                body += "\n".join(error["context"])
                body += "\n```\n"
                body += f"*Detected at: {error['timestamp']}*\n"

        body += f"""
### 📋 Environment Information
- **Monitor Version**: 1.0.0
- **Detection Time**: {datetime.now().isoformat()}
- **Container**: {container_name}
- **Error Threshold**: {self.error_threshold} errors

### 🔧 Suggested Actions
1. Check container logs: `docker logs {container_name} --tail 100`
2. Inspect container: `docker inspect {container_name}`
3. Restart if needed: `docker restart {container_name}`
4. Check resource usage: `docker stats {container_name}`

### 🏷️ Labels
This issue was automatically created by the Container Error Monitor.

---
*This is an automated issue. Please investigate and close when resolved.*
"""

        # Create issue via GitHub API
        url = f"https://api.github.com/repos/{self.github_repo}/issues"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        data = {
            "title": title,
            "body": body,
            "labels": ["bug", "auto-generated", "container-error", container_name],
            "assignees": ["qws941"],
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 201:
                issue_data = response.json()
                print(
                    f"✅ Created issue #{issue_data['number']}: {issue_data['html_url']}"
                )
                self.last_issue_time[container_name] = datetime.now()
                return True
            else:
                print(
                    f"❌ Failed to create issue: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            print(f"❌ Error creating GitHub issue: {e}")
            return False

    def monitor_container(self, container_name: str):
        """Monitor a single container for errors"""
        print(f"🔍 Monitoring {container_name}...")

        # Get recent logs
        logs = self.get_container_logs(container_name, "2m")

        if not logs:
            return

        # Extract errors
        errors = self.extract_errors(logs, container_name)

        if errors:
            print(f"⚠️ Found {len(errors)} error(s) in {container_name}")

            # Update error count
            if container_name not in self.error_counts:
                self.error_counts[container_name] = 0
            self.error_counts[container_name] += len(errors)

            # Create issue if threshold reached
            if self.error_counts[container_name] >= self.error_threshold:
                print(f"🚨 Error threshold reached for {container_name}")

                if self.create_github_issue(errors, container_name):
                    # Reset counter after successful issue creation
                    self.error_counts[container_name] = 0
                    self.seen_errors[container_name] = set()
        else:
            # Reset counter if no errors found
            if container_name in self.error_counts:
                self.error_counts[container_name] = 0

    def check_container_exists(self, container_name: str) -> bool:
        """Check if container exists"""
        try:
            cmd = f"docker inspect {container_name} --format '{{{{.Name}}}}'"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def run(self):
        """Main monitoring loop"""
        print(
            f"""
🚀 Container Error Monitor Started
📦 Monitoring: {', '.join(self.containers)}
⏱️ Interval: {self.monitor_interval} seconds
🎯 Error Threshold: {self.error_threshold} errors
📝 GitHub Repo: {self.github_repo}
"""
        )

        # Verify containers exist
        valid_containers = []
        for container in self.containers:
            if self.check_container_exists(container):
                valid_containers.append(container)
                print(f"✅ Found container: {container}")
            else:
                print(f"⚠️ Container not found: {container}")

        if not valid_containers:
            print("❌ No valid containers to monitor")
            return

        print(f"\n🎯 Monitoring {len(valid_containers)} container(s)...\n")

        # Main monitoring loop
        try:
            while True:
                for container in valid_containers:
                    self.monitor_container(container)

                # Clean old error hashes (older than 1 hour)
                current_time = datetime.now()
                for container in list(self.seen_errors.keys()):
                    if container in self.last_issue_time:
                        if current_time - self.last_issue_time[container] > timedelta(
                            hours=1
                        ):
                            self.seen_errors[container] = set()

                print(f"💤 Sleeping for {self.monitor_interval} seconds...")
                time.sleep(self.monitor_interval)

        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")


if __name__ == "__main__":
    monitor = ContainerErrorMonitor()
    monitor.run()
