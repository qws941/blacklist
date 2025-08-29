#!/bin/bash
# Generate Build Metadata for Dynamic Versioning
# This script creates comprehensive build information for CI/CD pipelines

set -euo pipefail

# Configuration
REPO_ROOT="${1:-.}"
OUTPUT_DIR="${REPO_ROOT}/build/metadata"
VERSION_SCRIPT="${REPO_ROOT}/scripts/version/dynamic-version.py"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Generating Dynamic Version Metadata${NC}"

# Generate version information
echo -e "${YELLOW}📊 Calculating dynamic version...${NC}"
if [[ -f "${VERSION_SCRIPT}" ]]; then
    python3 "${VERSION_SCRIPT}" --get-version --output-format json > "${OUTPUT_DIR}/version-info.json"
    VERSION=$(python3 "${VERSION_SCRIPT}" --get-version | grep "Next version:" | cut -d' ' -f3)
else
    # Fallback if script not available
    if [[ -f "${REPO_ROOT}/VERSION" ]]; then
        VERSION=$(cat "${REPO_ROOT}/VERSION")
    else
        VERSION="0.1.0"
    fi
    
    # Create basic version info
    cat > "${OUTPUT_DIR}/version-info.json" <<EOF
{
  "version": "${VERSION}",
  "build_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "git": {
    "commit": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
    "branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
    "build": "$(git rev-list --count HEAD 2>/dev/null || echo '0')"
  }
}
EOF
fi

echo -e "${GREEN}✅ Version: ${VERSION}${NC}"

# Generate build metadata
echo -e "${YELLOW}🏗️ Generating build metadata...${NC}"
cat > "${OUTPUT_DIR}/build-info.json" <<EOF
{
  "build_id": "${GITHUB_RUN_ID:-$(date +%s)}",
  "build_number": "${GITHUB_RUN_NUMBER:-0}",
  "build_url": "${GITHUB_SERVER_URL:-}/${GITHUB_REPOSITORY:-}/actions/runs/${GITHUB_RUN_ID:-}",
  "workflow": "${GITHUB_WORKFLOW:-local}",
  "actor": "${GITHUB_ACTOR:-$(whoami)}",
  "event": "${GITHUB_EVENT_NAME:-manual}",
  "ref": "${GITHUB_REF:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')}",
  "sha": "${GITHUB_SHA:-$(git rev-parse HEAD 2>/dev/null || echo 'unknown')}",
  "repository": "${GITHUB_REPOSITORY:-local/repo}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "timezone": "UTC"
}
EOF

# Generate Git metadata
echo -e "${YELLOW}📝 Collecting Git metadata...${NC}"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    cat > "${OUTPUT_DIR}/git-info.json" <<EOF
{
  "commit_hash": "$(git rev-parse HEAD)",
  "commit_hash_short": "$(git rev-parse --short HEAD)",
  "branch": "$(git rev-parse --abbrev-ref HEAD)",
  "tag": "$(git describe --tags --exact-match 2>/dev/null || echo '')",
  "last_tag": "$(git describe --tags --abbrev=0 2>/dev/null || echo '')",
  "commits_since_tag": $(git rev-list --count $(git describe --tags --abbrev=0 2>/dev/null || echo 'HEAD')..HEAD 2>/dev/null || echo 0),
  "commit_count": $(git rev-list --count HEAD),
  "last_commit_timestamp": "$(git log -1 --format=%cI)",
  "last_commit_message": $(git log -1 --format=%s | jq -R .),
  "last_commit_author": $(git log -1 --format=%an | jq -R .),
  "dirty": $(if [[ -n "$(git status --porcelain)" ]]; then echo "true"; else echo "false"; fi),
  "remote_url": "$(git config --get remote.origin.url || echo '')"
}
EOF
else
    cat > "${OUTPUT_DIR}/git-info.json" <<EOF
{
  "error": "Not a git repository",
  "commit_hash": "unknown",
  "branch": "unknown"
}
EOF
fi

# Generate environment metadata
echo -e "${YELLOW}🌍 Collecting environment metadata...${NC}"
cat > "${OUTPUT_DIR}/environment-info.json" <<EOF
{
  "hostname": "$(hostname)",
  "os": "$(uname -s)",
  "arch": "$(uname -m)",
  "kernel": "$(uname -r)",
  "user": "$(whoami)",
  "pwd": "$(pwd)",
  "shell": "${SHELL:-unknown}",
  "ci": "${CI:-false}",
  "github_actions": "${GITHUB_ACTIONS:-false}",
  "node_version": "$(node --version 2>/dev/null || echo 'not installed')",
  "python_version": "$(python3 --version 2>/dev/null || echo 'not installed')",
  "docker_version": "$(docker --version 2>/dev/null || echo 'not installed')"
}
EOF

# Generate Docker metadata for multi-image builds
echo -e "${YELLOW}🐳 Generating Docker metadata...${NC}"
IMAGES=("app" "postgres" "redis")
for image in "${IMAGES[@]}"; do
    cat > "${OUTPUT_DIR}/${image}-docker-info.json" <<EOF
{
  "image_name": "${image}",
  "registry": "registry.jclee.me",
  "full_name": "registry.jclee.me/blacklist-${image}",
  "tags": [
    "latest",
    "${VERSION}",
    "${VERSION}-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
    "build-${GITHUB_RUN_NUMBER:-$(date +%s)}"
  ],
  "dockerfile": "${image}.Dockerfile",
  "context": ".",
  "build_args": {
    "VERSION": "${VERSION}",
    "BUILD_DATE": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "VCS_REF": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
  },
  "labels": {
    "org.opencontainers.image.version": "${VERSION}",
    "org.opencontainers.image.created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "org.opencontainers.image.revision": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "org.opencontainers.image.source": "${GITHUB_SERVER_URL:-}/${GITHUB_REPOSITORY:-}",
    "org.opencontainers.image.url": "${GITHUB_SERVER_URL:-}/${GITHUB_REPOSITORY:-}",
    "org.opencontainers.image.title": "Blacklist ${image^} Service",
    "org.opencontainers.image.description": "Blacklist Management System - ${image^} Service"
  }
}
EOF
done

# Create consolidated metadata file
echo -e "${YELLOW}📋 Creating consolidated metadata...${NC}"
python3 -c "
import json
import os
from pathlib import Path

metadata_dir = Path('${OUTPUT_DIR}')
consolidated = {}

for json_file in metadata_dir.glob('*.json'):
    key = json_file.stem.replace('-', '_')
    try:
        with open(json_file, 'r') as f:
            consolidated[key] = json.load(f)
    except Exception as e:
        consolidated[key] = {'error': str(e)}

with open(metadata_dir / 'consolidated-metadata.json', 'w') as f:
    json.dump(consolidated, f, indent=2, ensure_ascii=False)
"

# Generate version files for each service
echo -e "${YELLOW}📄 Creating service-specific version files...${NC}"
for image in "${IMAGES[@]}"; do
    echo "${VERSION}" > "${OUTPUT_DIR}/${image}-VERSION"
done

# Create summary
echo -e "${YELLOW}📊 Creating build summary...${NC}"
cat > "${OUTPUT_DIR}/build-summary.txt" <<EOF
🚀 Dynamic Version Build Summary
================================

Version: ${VERSION}
Build Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Build ID: ${GITHUB_RUN_ID:-$(date +%s)}
Git Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')
Git Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')

📦 Docker Images:
$(for img in "${IMAGES[@]}"; do
    echo "  - registry.jclee.me/blacklist-${img}:${VERSION}"
done)

📁 Generated Files:
$(ls -la "${OUTPUT_DIR}" | awk 'NR>1 {print "  - " $9}' | grep -v "^\s*-\s*$")

🔍 Metadata Location: ${OUTPUT_DIR}
EOF

# Output summary
echo -e "${GREEN}✅ Build metadata generated successfully!${NC}"
echo -e "${BLUE}📊 Summary:${NC}"
cat "${OUTPUT_DIR}/build-summary.txt"

# Export key variables for GitHub Actions
if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    echo "VERSION=${VERSION}" >> "${GITHUB_OUTPUT}"
    echo "BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "${GITHUB_OUTPUT}"
    echo "GIT_COMMIT=$(git rev-parse --short HEAD)" >> "${GITHUB_OUTPUT}"
    echo "METADATA_DIR=${OUTPUT_DIR}" >> "${GITHUB_OUTPUT}"
fi

echo -e "${GREEN}🎉 Dynamic version metadata generation complete!${NC}"