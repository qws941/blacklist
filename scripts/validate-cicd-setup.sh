#!/bin/bash
# CI/CD Pipeline Validation Script
# 동적 버전 관리 및 멀티 이미지 파이프라인 검증

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 CI/CD Pipeline Validation${NC}"
echo "=================================="

VALIDATION_PASSED=true

# Function to check file existence
check_file() {
    local file="$1"
    local description="$2"
    
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $description: $file${NC}"
        return 0
    else
        echo -e "${RED}❌ $description: $file (MISSING)${NC}"
        VALIDATION_PASSED=false
        return 1
    fi
}

# Function to check directory existence
check_directory() {
    local dir="$1"
    local description="$2"
    
    if [[ -d "$dir" ]]; then
        echo -e "${GREEN}✅ $description: $dir${NC}"
        return 0
    else
        echo -e "${RED}❌ $description: $dir (MISSING)${NC}"
        VALIDATION_PASSED=false
        return 1
    fi
}

# Function to check script executability
check_executable() {
    local script="$1"
    local description="$2"
    
    if [[ -x "$script" ]]; then
        echo -e "${GREEN}✅ $description: executable${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $description: making executable${NC}"
        chmod +x "$script"
        return 0
    fi
}

echo -e "\n${YELLOW}📋 1. Checking Core Files${NC}"
echo "----------------------------"

# Check Dockerfiles
check_file "Dockerfile" "Main Application Dockerfile"
check_file "postgres.Dockerfile" "PostgreSQL Dockerfile"
check_file "redis.Dockerfile" "Redis Dockerfile"

# Check Version Files
check_file "VERSION" "Version File"
check_file "scripts/version/dynamic-version.py" "Dynamic Version Script"
check_file "scripts/version/generate-build-metadata.sh" "Build Metadata Generator"

echo -e "\n${YELLOW}📁 2. Checking Directory Structure${NC}"
echo "--------------------------------"

# Check directories
check_directory ".github/workflows" "GitHub Workflows Directory"
check_directory "scripts/version" "Version Scripts Directory"

echo -e "\n${YELLOW}⚙️ 3. Checking GitHub Actions Workflows${NC}"
echo "---------------------------------------"

# Check workflows
check_file ".github/workflows/advanced-cicd.yml" "Advanced CI/CD Workflow"
check_file ".github/workflows/dynamic-version.yml" "Dynamic Version Workflow"
check_file ".github/SETUP-SECRETS.md" "Secrets Setup Guide"

echo -e "\n${YELLOW}🔧 4. Checking Script Executability${NC}"
echo "-----------------------------------"

# Make scripts executable
if [[ -f "scripts/version/dynamic-version.py" ]]; then
    check_executable "scripts/version/dynamic-version.py" "Dynamic Version Script"
fi

if [[ -f "scripts/version/generate-build-metadata.sh" ]]; then
    check_executable "scripts/version/generate-build-metadata.sh" "Build Metadata Generator"
fi

echo -e "\n${YELLOW}🐍 5. Testing Dynamic Version Script${NC}"
echo "------------------------------------"

if [[ -f "scripts/version/dynamic-version.py" ]]; then
    echo "Testing version calculation..."
    if python3 scripts/version/dynamic-version.py --get-version; then
        echo -e "${GREEN}✅ Dynamic version script working${NC}"
    else
        echo -e "${RED}❌ Dynamic version script failed${NC}"
        VALIDATION_PASSED=false
    fi
else
    echo -e "${RED}❌ Dynamic version script not found${NC}"
    VALIDATION_PASSED=false
fi

echo -e "\n${YELLOW}📝 6. Validating Docker Configuration${NC}"
echo "-------------------------------------"

# Check if main Dockerfile has proper structure
if [[ -f "Dockerfile" ]]; then
    if grep -q "FROM python:3.11-slim as builder" Dockerfile; then
        echo -e "${GREEN}✅ Multi-stage build configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Single-stage Dockerfile detected${NC}"
    fi
    
    if grep -q "USER appuser" Dockerfile; then
        echo -e "${GREEN}✅ Non-root user configured${NC}"
    else
        echo -e "${RED}❌ Running as root user${NC}"
        VALIDATION_PASSED=false
    fi
    
    if grep -q "HEALTHCHECK" Dockerfile; then
        echo -e "${GREEN}✅ Health check configured${NC}"
    else
        echo -e "${YELLOW}⚠️  No health check found${NC}"
    fi
fi

echo -e "\n${YELLOW}🔍 7. Validating Workflow Configuration${NC}"
echo "--------------------------------------"

if [[ -f ".github/workflows/advanced-cicd.yml" ]]; then
    if grep -q "registry.jclee.me" ".github/workflows/advanced-cicd.yml"; then
        echo -e "${GREEN}✅ Private registry configured${NC}"
    else
        echo -e "${RED}❌ Private registry not configured${NC}"
        VALIDATION_PASSED=false
    fi
    
    if grep -q "matrix:" ".github/workflows/advanced-cicd.yml"; then
        echo -e "${GREEN}✅ Multi-image build matrix configured${NC}"
    else
        echo -e "${RED}❌ Multi-image build not configured${NC}"
        VALIDATION_PASSED=false
    fi
    
    if grep -q "paths-filter" ".github/workflows/advanced-cicd.yml"; then
        echo -e "${GREEN}✅ Change detection configured${NC}"
    else
        echo -e "${RED}❌ Change detection not configured${NC}"
        VALIDATION_PASSED=false
    fi
fi

echo -e "\n${YELLOW}🧪 8. Testing Build Metadata Generation${NC}"
echo "----------------------------------------"

if [[ -f "scripts/version/generate-build-metadata.sh" ]]; then
    echo "Testing metadata generation (dry run)..."
    if bash scripts/version/generate-build-metadata.sh . > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Build metadata generation working${NC}"
        if [[ -f "build/metadata/consolidated-metadata.json" ]]; then
            echo -e "${GREEN}✅ Metadata files generated${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Build metadata generation had issues (check dependencies)${NC}"
    fi
fi

echo -e "\n${YELLOW}📊 9. Validation Summary${NC}"
echo "------------------------"

if [[ "$VALIDATION_PASSED" == "true" ]]; then
    echo -e "${GREEN}🎉 All validations passed!${NC}"
    echo -e "${GREEN}✅ CI/CD pipeline is ready to use${NC}"
    echo ""
    echo -e "${BLUE}📝 Next Steps:${NC}"
    echo "1. Configure GitHub Secrets (see .github/SETUP-SECRETS.md)"
    echo "2. Push code to trigger the pipeline"
    echo "3. Monitor GitHub Actions for successful builds"
    echo ""
    echo -e "${BLUE}🚀 Usage:${NC}"
    echo "- Automatic: Push code changes to trigger builds"
    echo "- Manual: Run workflows from GitHub Actions tab"
    echo "- Version: Follows semantic versioning based on commit messages"
else
    echo -e "${RED}❌ Some validations failed${NC}"
    echo -e "${YELLOW}Please fix the issues above before using the pipeline${NC}"
    exit 1
fi

echo -e "\n${BLUE}🔧 CI/CD Pipeline Features:${NC}"
echo "- 🔄 Dynamic version management with semantic versioning"
echo "- 🐳 Multi-image builds (app, postgres, redis)"
echo "- 📊 Comprehensive change detection"
echo "- 🔐 Private registry integration"
echo "- 🛡️ Security scanning with Trivy"
echo "- 📋 Detailed build metadata generation"
echo "- 🏷️ Automatic GitHub releases"
echo "- ⚡ Parallel builds for performance"