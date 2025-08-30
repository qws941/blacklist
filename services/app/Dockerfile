# Multi-stage build for production optimization
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY src/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Build arguments for version information
ARG VERSION
ARG BUILD_NUMBER
ARG VCS_REF
ARG BUILDTIME

# Set version environment variables
ENV VERSION=${VERSION}
ENV BUILD_NUMBER=${BUILD_NUMBER}
ENV VCS_REF=${VCS_REF}
ENV BUILDTIME=${BUILDTIME}

# Create non-root user for security
RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser appuser

# Install runtime dependencies + dependency management tools
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY src/ ./src/
COPY src/main.py .
COPY gunicorn.conf.py .

# Add dependency wait script for independent operation
COPY <<'EOF' ./wait-for-services.sh
#!/bin/bash
set -e

# Default values
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
REDIS_HOST=${REDIS_HOST:-localhost}  
REDIS_PORT=${REDIS_PORT:-6379}
MAX_ATTEMPTS=${DEPENDENCY_WAIT_MAX_ATTEMPTS:-30}
WAIT_INTERVAL=${DEPENDENCY_WAIT_INTERVAL:-2}

echo "🔍 Waiting for dependencies..."
echo "PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT"
echo "Redis: $REDIS_HOST:$REDIS_PORT"

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
attempt=1
while [ $attempt -le $MAX_ATTEMPTS ]; do
    if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    
    if [ $attempt -eq $MAX_ATTEMPTS ]; then
        echo "❌ PostgreSQL not available after $MAX_ATTEMPTS attempts"
        exit 1
    fi
    
    echo "⏳ PostgreSQL not ready (attempt $attempt/$MAX_ATTEMPTS), waiting..."
    sleep $WAIT_INTERVAL
    attempt=$((attempt + 1))
done

# Wait for Redis
echo "⏳ Waiting for Redis..."
attempt=1
while [ $attempt -le $MAX_ATTEMPTS ]; do
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
        echo "✅ Redis is ready"
        break
    fi
    
    if [ $attempt -eq $MAX_ATTEMPTS ]; then
        echo "❌ Redis not available after $MAX_ATTEMPTS attempts"
        exit 1
    fi
    
    echo "⏳ Redis not ready (attempt $attempt/$MAX_ATTEMPTS), waiting..."
    sleep $WAIT_INTERVAL
    attempt=$((attempt + 1))
done

echo "🚀 All dependencies ready, starting application..."
EOF

# Add smart startup script
COPY <<'EOF' ./smart-start.sh
#!/bin/bash
set -e

echo "🏁 Smart Application Startup"
echo "Version: ${VERSION:-unknown}"
echo "Build: ${BUILD_NUMBER:-unknown}"

# Check if dependency waiting is enabled
if [ "${SKIP_DEPENDENCY_WAIT:-false}" != "true" ]; then
    ./wait-for-services.sh
else
    echo "⚠️  Dependency wait skipped"
fi

# Start the application
echo "🚀 Starting Gunicorn application server..."
exec gunicorn --config gunicorn.conf.py main:app
EOF

# Make scripts executable
RUN chmod +x ./wait-for-services.sh ./smart-start.sh

# Create necessary directories
RUN mkdir -p /app/instance /app/logs /app/data && \
    chown -R appuser:appuser /app

# Set PATH for user packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 2542

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:2542/health || exit 1

# Use smart startup script for independent operation
CMD ["./smart-start.sh"]