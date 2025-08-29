#!/bin/bash
# Quick start script - assumes images are already pulled

set -e

# Create network if not exists
docker network create blacklist-network 2>/dev/null || true

# Start services
docker-compose up -d

echo "✅ Services started"
docker-compose ps