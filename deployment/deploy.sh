#!/bin/bash
# Deploy script for blacklist application with private registry

set -e

REGISTRY="registry.jclee.me"
REGISTRY_USER="admin"
REGISTRY_PASSWORD="bingogo1"

echo "🔐 Logging into private registry..."
echo "${REGISTRY_PASSWORD}" | docker login ${REGISTRY} -u ${REGISTRY_USER} --password-stdin

echo "📥 Pulling custom images from private registry..."
docker pull ${REGISTRY}/blacklist-postgres:latest
docker pull ${REGISTRY}/blacklist-app:latest

# Redis는 공식 이미지 사용
echo "📥 Pulling Redis..."
docker pull redis:alpine

echo "🌐 Creating network if not exists..."
docker network create blacklist-network 2>/dev/null || true

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

echo "✅ Deployment complete!"
echo ""
echo "Services:"
echo "  - App: http://localhost:2542"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "Check status: docker-compose ps"
echo "View logs: docker-compose logs -f app"