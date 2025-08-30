# Blacklist Management System

Enterprise threat intelligence platform for collecting, processing, and managing threat data from multiple sources.

## 🚀 Quick Start

### Using Docker Compose Orchestration (Recommended)
```bash
# Production deployment with full orchestration
./scripts/deploy.sh production --backup

# Staging environment deployment
./scripts/deploy.sh staging

# Check system status
./scripts/deploy.sh status

# View service logs
./scripts/deploy.sh logs app
```

### Available Compose Configurations
- `docker-compose.yml` - Development environment
- `docker-compose.production.yml` - Full production setup with monitoring
- `docker-compose.resilient.yml` - High-resilience configuration
- `docker-compose.stress.yml` - Resource-constrained testing

### Quick Commands
```bash
# Production start
docker-compose -f docker-compose.production.yml up -d

# Check all services
docker-compose -f docker-compose.production.yml ps

# Health check
curl http://localhost:2542/health | jq
```

Access the application at: http://localhost:2542  
Monitoring dashboard: [monitoring/dashboard.html](./monitoring/dashboard.html)

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

## 📋 Features

- **Threat Intelligence Collection**: Automated data collection from Regtech and Secudium
- **Real-time Monitoring**: System health monitoring with container error detection
- **Database Management**: PostgreSQL with pre-initialized schema (7 core tables)
- **Caching Layer**: Redis integration for performance optimization
- **RESTful API**: Comprehensive API endpoints for threat data management
- **Fallback System**: Three-tier application startup (Full → Minimal → Emergency)

## 🏗️ Architecture

### Services
- **Flask Application**: Main web service (port 32542)
- **PostgreSQL Database**: Data persistence (port 5432)
- **Redis Cache**: Session and data caching (port 32544)

### Key Components
```
src/
├── api/                    # API endpoints
├── core/                   # Core business logic
├── models/                 # Data models
├── utils/                  # Utilities and helpers
└── web/                    # Web interface
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
POSTGRES_HOST=blacklist-postgres
POSTGRES_PORT=5432
POSTGRES_DB=blacklist
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=blacklist-redis
REDIS_PORT=6379

# Application
FLASK_ENV=production
PORT=2542
```

## 📊 Database Schema

Core tables:
- `blacklist_ips` - Threat IP addresses
- `system_logs` - Application logs
- `monitoring_data` - Performance metrics
- `api_keys` - API authentication
- `collection_history` - Data collection audit
- `user_activities` - User action tracking
- `notification_settings` - Alert configuration

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific tests
pytest tests/unit/
```

## 📦 Complete CI/CD Pipeline

### Automated Pipeline (GitHub Actions)
The system includes a complete CI/CD pipeline with:
- **Automated Testing**: Code formatting, linting, unit tests, security scans
- **Multi-Image Build**: Application, PostgreSQL, and Redis images
- **Staged Deployment**: Staging validation → Production deployment
- **Health Verification**: Comprehensive health checks and rollback capability

### Pipeline Workflow
```bash
git push origin main
# Triggers:
# 1. Test & Security Scan
# 2. Build & Push to registry.jclee.me
# 3. Deploy to Staging
# 4. Integration Tests
# 5. Deploy to Production
# 6. Health Verification
```

### Manual Deployment Options
```bash
# Complete production deployment
./scripts/deploy.sh production --backup

# Build and push images manually
docker build -f Dockerfile.simple -t registry.jclee.me/blacklist-app:latest .
docker build -f postgres.Dockerfile -t registry.jclee.me/blacklist-postgres:latest .  
docker build -f redis.Dockerfile -t registry.jclee.me/blacklist-redis:latest .
docker push registry.jclee.me/blacklist-app:latest
```

### Zero-Downtime Deployment
- **Watchtower Integration**: Automatic image updates every 5 minutes
- **Rolling Updates**: Service restart without downtime
- **Health Checks**: Comprehensive service validation
- **Backup Integration**: Pre-deployment database backups

## 🔍 Health Checks

```bash
# Application health
curl http://localhost:32542/health | jq

# Database connection test
docker exec -it blacklist-postgres psql -U postgres -d blacklist -c "SELECT COUNT(*) FROM blacklist_ips;"
```

## 📝 API Documentation

### Endpoints
- `GET /` - Service information
- `GET /health` - Health status with database connection
- `POST /api/blacklist` - Add threat data
- `GET /api/monitoring` - System metrics

## 🛠️ Development

### Code Style
- Python 3.11+
- Flask 3.0.0
- PostgreSQL 15
- Redis latest

### Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

Proprietary - All rights reserved

## 🔗 Links

- **Documentation**: See [CLAUDE.md](./CLAUDE.md) for detailed development guide
- **Container Monitoring**: `scripts/container-error-monitor.py`
- **Independence Tests**: `scripts/run-independence-tests.sh`

## 🎯 Orchestration Features

### Service Orchestration
- **Dependency Management**: Services start in proper order (DB → Cache → App)
- **Health Monitoring**: Continuous health checks with automatic restart
- **Resource Management**: CPU and memory limits with reservation guarantees
- **Network Isolation**: Dedicated bridge network with subnet configuration
- **Data Persistence**: Persistent volumes with host path binding

### Monitoring & Alerting
- **Real-time Dashboard**: Web-based monitoring with charts and metrics
- **Health Monitor Service**: Dedicated monitoring container with Slack integration
- **Watchtower Management**: Automated image updates with lifecycle hooks
- **Log Aggregation**: Centralized logging with JSON structured output

### Deployment Scenarios
```bash
# Different deployment scenarios
./scripts/deploy.sh production    # Full production with monitoring
./scripts/deploy.sh staging      # Lightweight staging environment
./scripts/deploy.sh rollback     # Emergency rollback to previous version
./scripts/deploy.sh health       # Health check validation only
```

## ⚠️ Troubleshooting

### Pipeline Issues
```bash
# Check GitHub Actions workflow status
# Verify registry.jclee.me access
# Review deployment logs: ./scripts/deploy.sh logs

# Manual intervention
./scripts/deploy.sh production --force --skip-tests
```

### Container Orchestration
```bash
# Network issues
docker network create blacklist-network

# Service dependencies
docker-compose -f docker-compose.production.yml up -d --remove-orphans

# Resource constraints
docker system prune -f && docker volume prune -f
```

### Service Discovery
- **Application**: http://localhost:2542
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:32544  
- **Watchtower API**: localhost:8080
- **Monitoring Dashboard**: ./monitoring/dashboard.html

### Quick Fixes
```bash
# Complete system reset
./scripts/deploy.sh production --force --backup

# Logs analysis
./scripts/deploy.sh logs | grep -i error

# Health verification
curl -f http://localhost:2542/health --max-time 15
```

---
**Complete Pipeline Architecture**: GitHub Actions → registry.jclee.me → Watchtower → Zero-downtime Updates  
**Last Updated**: 2025-08-30 (Pipeline v2.0 with Full Orchestration)