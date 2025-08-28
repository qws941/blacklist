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

## Development Environment Setup

### Python Environment
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate     # Windows

# Install dependencies from virtual environment
# Note: No requirements.txt found - dependencies managed through .venv/
pip install flask pytest requests  # Common dependencies based on codebase analysis
```

### Environment Configuration
- Use existing `.env` file or create from template
- Key environment variables:
  - `REGTECH_USERNAME`, `REGTECH_PASSWORD`: External API credentials
  - `SECUDIUM_USERNAME`, `SECUDIUM_PASSWORD`: External API credentials  
  - `SECRET_KEY`: Flask application secret
  - `JWT_SECRET_KEY`: JWT token encryption key

### Application Startup
```bash
# The application appears to run as Python modules
# Entry points are in src/ but no main runner script found
# Likely runs through Flask development server or WSGI
export FLASK_APP=src
export FLASK_ENV=development
flask run
```

### Database Setup
```bash
# Initialize SQLite databases (if needed)
# Databases are auto-created in instance/ directory:
# - blacklist.db: Main threat intelligence data
# - api_keys.db: API key management
# - monitoring.db: System monitoring data
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

## Container Environment

### Docker Services
The application runs with multiple containerized services:

```bash
# Container monitoring (docker-compose.monitor.yml)
docker-compose -f docker-compose.monitor.yml up -d

# Main services (implied from container monitor config):
# - blacklist-app: Main Flask application
# - blacklist-postgres: PostgreSQL database  
# - blacklist-redis: Redis cache server
```

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

## Deployment and Operations

### Container Deployment
```bash
# Start container monitoring stack
docker-compose -f docker-compose.monitor.yml up -d

# Check container status
docker ps | grep blacklist

# View container logs
docker logs blacklist-app
docker logs blacklist-postgres  
docker logs blacklist-redis
```

### System Monitoring
```bash
# Monitor error monitoring service
python3 scripts/container-error-monitor.py

# View real-time logs
tail -f logs/*.json
tail -f logs/*_errors.log

# Check automated component status
ls -la logs/ | grep -E "(json|log)$"
```

### Operational Tasks
```bash
# Collection management through configuration
# Edit instance/collection_config.json to enable/disable sources

# Database maintenance
# SQLite databases auto-managed in instance/
# PostgreSQL managed through container

# Security management
# API keys stored in instance/api_keys.db
# Encrypted credentials in instance/credentials.enc
```