# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Blacklist Management System** is an enterprise threat intelligence platform that collects, processes, and manages threat data from multiple sources. The system operates as a Flask-based web application with microservice architecture components for security monitoring and threat intelligence collection.

### Key Components

- **Main Application**: Flask web application with API endpoints and monitoring dashboards
- **Data Collection**: Automated threat intelligence collection from Regtech and Secudium sources  
- **Database Layer**: SQLite databases for blacklist data, monitoring, and API key management
- **Container Monitoring**: Automated error detection and GitHub issue creation system
- **Caching Layer**: Redis integration for performance optimization
- **Persistent Storage**: PostgreSQL for advanced data operations and analytics

## Development Commands

### Docker Development (Primary Method)
```bash
# Start all services (PostgreSQL, Redis, Flask app)
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f blacklist-app
docker-compose logs --tail=50 blacklist-postgres

# Rebuild application after code changes
docker-compose up -d --build blacklist-app

# Check container health status
docker-compose ps
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run application locally (requires PostgreSQL and Redis)
python main.py

# Run with gunicorn (production)
gunicorn --config gunicorn.conf.py main:app
```

### Testing & Health Checks
```bash
# Test health endpoint
curl http://localhost:32542/health | jq

# Test main endpoint  
curl http://localhost:32542/ | jq

# Run tests
python -m pytest tests/
```

### Database Management
```bash
# Connect to PostgreSQL
docker exec -it blacklist-postgres psql -U postgres -d blacklist

# View tables
\dt

# Check blacklist entries
SELECT * FROM blacklist_ips;
```

### Environment Variables
```bash
# Database
POSTGRES_HOST=blacklist-postgres  # or localhost for local dev
POSTGRES_PORT=5432
POSTGRES_DB=blacklist
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=blacklist-redis  # or localhost for local dev
REDIS_PORT=6379

# Application
FLASK_ENV=production
PORT=2542
```

## Application Architecture

### Directory Structure
```
src/
├── api/                    # API route modules
│   ├── collection/        # Data collection endpoints
│   └── monitoring/        # System monitoring APIs
├── core/                  # Core application logic
│   ├── app/              # Flask application factory
│   ├── automation/       # Automated processes
│   ├── blacklist_unified/ # Main blacklist processing
│   ├── collection_manager/ # Data collection orchestration
│   ├── collectors/       # External data source connectors
│   ├── database/         # Database abstraction layer
│   ├── monitoring/       # System health monitoring
│   ├── routes/           # HTTP route handlers
│   ├── services/         # Business logic services
│   └── utils/            # Shared utilities
├── models/               # Data models and schemas
├── utils/                # Advanced utilities
│   ├── advanced_cache/   # Caching implementations
│   ├── decorators/       # Function decorators
│   ├── error_handler/    # Error handling utilities
│   ├── memory/          # Memory management
│   └── security/        # Security utilities
└── web/                 # Web interface components
```

### Key Data Files
- `instance/`: SQLite databases and JSON configuration files
- `data/`: Raw data storage and exports
- `logs/`: Application and system logs with structured JSON format

## Container Architecture

### Docker Services
The application uses a microservices architecture with three main components:

1. **PostgreSQL Database** (`blacklist-postgres`)
   - Custom image with pre-initialized schema (`postgres.Dockerfile`)
   - 7 core tables: blacklist_ips, system_logs, monitoring_data, api_keys, collection_history, user_activities, notification_settings
   - Runs on port 5432

2. **Redis Cache** (`blacklist-redis`)
   - Session and data caching
   - Runs on port 32544 (mapped from 6379)

3. **Flask Application** (`blacklist-app`)
   - Main entry: `main.py` with fallback logic (full → minimal → emergency mode)
   - Custom Docker image built from `Dockerfile.simple`
   - Runs on port 32542 (mapped from 2542)

### Application Entry Flow
```
main.py
├── Try: src.core.main.create_app() [Full Mode]
├── Except: src.core.minimal_app.create_minimal_app() [Minimal Mode]
└── Fallback: Emergency Flask app with /health endpoint only
```

### Network Configuration
- All services communicate through `blacklist-network` (Docker bridge network)
- External access ports:
  - Application: 32542 → 2542
  - PostgreSQL: 5432 → 5432
  - Redis: 32544 → 6379

### Container Error Monitoring
- Automated monitoring script: `scripts/container-error-monitor.py`
- Monitors container logs for error patterns
- Auto-creates GitHub issues for critical errors
- Configurable error thresholds and monitoring intervals

### Automated Components
Based on log analysis, the system runs several automated modules:
- **AutomationBackupManager**: Automated backup operations
- **AutonomousMonitor**: Self-monitoring system components
- **KoreanAlertSystem**: Localized alerting system
- **PredictiveEngine**: AI-powered prediction and analysis
- **API Monitoring**: Continuous API health monitoring

## Data Collection System

### Collection Sources
- **Regtech**: Threat intelligence feed
- **Secudium**: Security data provider

### Collection Configuration
```json
// instance/collection_config.json structure:
{
  "collection_enabled": boolean,
  "sources": {
    "regtech": {"enabled": boolean, "enabled_at": timestamp},
    "secudium": {"enabled": boolean, "enabled_at": timestamp}
  },
  "protection_mode": "FORCE_DISABLE|NORMAL",
  "restart_protection": {...}
}
```

### Collection Management
- Manual enable/disable controls with protection mechanisms
- Automatic restart protection to prevent runaway collection
- Comprehensive audit logging of collection state changes
- Force disable mode for emergency stop functionality

## Testing Framework

### Test Organization
```
tests/
├── integration/          # Integration test suites
├── logging_tests/       # Logging system tests
├── security/            # Security validation tests
├── ui/                  # User interface tests
├── unit/                # Unit test modules
└── utils/               # Test utilities and helpers
```

### Independence Testing
- Comprehensive Docker service independence tests
- Script location: `scripts/run-independence-tests.sh`
- Tests individual services: blacklist, redis, postgresql, monitoring
- Generates HTML and text reports in `logs/independence-tests/`

```bash
# Run all independence tests  
./scripts/run-independence-tests.sh

# Test specific service
./scripts/test-blacklist-service.sh
./scripts/test-redis-service.sh
./scripts/test-postgresql-service.sh

### Python Testing
```bash
# Run tests with pytest (pytest cache found in .pytest_cache)
pytest                    # Run all tests
pytest -v                # Verbose output
pytest tests/unit/       # Run specific test directory
pytest -k "test_name"    # Run specific test pattern

# Test organization mirrors src/ structure:
# tests/unit/           - Unit tests
# tests/integration/    - Integration tests  
# tests/security/       - Security tests
# tests/ui/            - UI/Frontend tests
```

## Security Considerations

### Credential Management  
- Environment variables for external API credentials
- Encrypted credential storage: `instance/credentials.enc`
- JWT-based authentication with configurable secret keys
- API key management system with dedicated database

### Data Protection
- SQLite databases with appropriate file permissions
- Structured logging without credential exposure
- Container isolation for service security
- Automated monitoring for security-related errors

## Monitoring and Alerting

### System Monitoring
- Container health monitoring with Docker integration
- Error pattern detection with configurable thresholds
- Automated GitHub issue creation for critical alerts
- Performance monitoring and resource tracking

### Log Management
- Structured JSON logging throughout the application
- Separate log files for different components
- Error log aggregation and analysis
- Independence test reporting with detailed metrics

## Development Workflows

### Code Organization
- Modular architecture with clear separation of concerns
- Service-oriented design with dedicated modules
- Utility functions organized by functionality
- Configuration-driven feature enablement

### Database Operations
- Multiple database backends (SQLite, PostgreSQL, Redis)
- Configuration-based database selection
- Automated schema management and migrations
- Performance monitoring for database operations

### API Development
- RESTful API design with consistent routing
- Authentication middleware integration
- Request/response logging and monitoring
- Error handling with structured responses

## Production Deployment

### Building Images
```bash
# Build and push to registry
docker build -f Dockerfile.simple -t registry.jclee.me/blacklist-app:latest .
docker build -f postgres.Dockerfile -t registry.jclee.me/blacklist-postgres:latest .
docker push registry.jclee.me/blacklist-app:latest
docker push registry.jclee.me/blacklist-postgres:latest
```

### Production Configuration Files
- `docker-compose.production.yml`: Production docker-compose configuration
- `.env.production`: Production environment variables
- `gunicorn.conf.py`: Gunicorn WSGI server configuration
- `monitoring-dashboard.html`: Real-time monitoring dashboard

### Common Issues & Solutions

#### Container Won't Start
- Check if using correct Dockerfile (`Dockerfile.simple`, not bare `python:3.11-slim`)
- Ensure all required source files are present
- Verify PostgreSQL and Redis are healthy before app starts

#### Database Connection Failed
- Ensure PostgreSQL container is running and healthy
- Check network connectivity between containers
- Verify environment variables are correctly set

#### Port Already in Use
- Default ports: 32542 (app), 5432 (postgres), 32544 (redis)
- Modify port mappings in docker-compose.yml if needed