# Blacklist Management System

Enterprise threat intelligence platform for collecting, processing, and managing threat data from multiple sources.

## 🚀 Quick Start

### Using Docker (Recommended)
```bash
# First time setup (pulls custom images from private registry)
./deploy.sh

# Or quick start (if images already pulled)
./start.sh

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

Access the application at: http://localhost:2542

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

## 📦 Docker Images

### Build Custom Images
```bash
# Build application
docker build -f Dockerfile.simple -t blacklist-app:latest .

# Build PostgreSQL with schema
docker build -f postgres.Dockerfile -t blacklist-postgres:latest .
```

### Production Deployment
```bash
# Use production compose file
docker-compose -f docker-compose.production.yml up -d
```

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

## ⚠️ Troubleshooting

### Container Issues
- Ensure Docker network exists: `docker network create blacklist-network`
- Check container health: `docker-compose ps`
- Review logs: `docker-compose logs --tail=50 [service-name]`

### Database Connection
- Verify PostgreSQL is running: `docker ps | grep postgres`
- Test connection: `docker exec -it blacklist-postgres pg_isready`

### Port Conflicts
- Application: 32542
- PostgreSQL: 5432
- Redis: 32544

Modify port mappings in `docker-compose.yml` if needed.

---
Last Updated: 2025-08-28