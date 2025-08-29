#!/bin/bash
# Build and push Docker images for blacklist application

set -e

REGISTRY="registry.jclee.me"
VERSION="${1:-latest}"

echo "🔨 Building Docker images..."

# Build application image
echo "📦 Building blacklist-app:${VERSION}..."
docker build -f Dockerfile -t ${REGISTRY}/blacklist-app:${VERSION} .
docker tag ${REGISTRY}/blacklist-app:${VERSION} ${REGISTRY}/blacklist-app:latest

# Build PostgreSQL image
echo "📦 Building blacklist-postgres:${VERSION}..."
docker build -f postgres.Dockerfile -t ${REGISTRY}/blacklist-postgres:${VERSION} .
docker tag ${REGISTRY}/blacklist-postgres:${VERSION} ${REGISTRY}/blacklist-postgres:latest

# Build Redis image
echo "📦 Building blacklist-redis:${VERSION}..."
docker build -f redis.Dockerfile -t ${REGISTRY}/blacklist-redis:${VERSION} . 2>/dev/null || {
    echo "ℹ️ No custom Redis Dockerfile found, using official image"
    docker pull redis:alpine
    docker tag redis:alpine ${REGISTRY}/blacklist-redis:${VERSION}
    docker tag redis:alpine ${REGISTRY}/blacklist-redis:latest
}

echo "✅ Build completed"

# Push images if requested
if [ "$2" = "push" ]; then
    echo "🚀 Pushing images to registry..."
    docker push ${REGISTRY}/blacklist-app:${VERSION}
    docker push ${REGISTRY}/blacklist-app:latest
    docker push ${REGISTRY}/blacklist-postgres:${VERSION}
    docker push ${REGISTRY}/blacklist-postgres:latest
    docker push ${REGISTRY}/blacklist-redis:${VERSION}
    docker push ${REGISTRY}/blacklist-redis:latest
    echo "✅ Push completed"
fi

echo "📝 Usage:"
echo "  Development: docker-compose up -d"
echo "  Production:  docker-compose -f docker-compose.production.yml up -d"