# 🧪 Jane AI Platform ├── unit/                  # Unit tests by component
│   ├── spellbook/         # Spellbook backend unit tests
│   ├── spellbook-client/  # Spellbook client unit tests
│   ├── website/           # Website unit tests
│   └── common/            # Common utility unit testsst Suite

## Overview
This directory contains all testing utilities for the Jane AI Platform, organized by test type and purpose.

## Directory Structure

```
tests/
├── README.md              # This file
├── run_all_tests.sh       # Master test runner
├── integration/           # Integration and system tests
│   ├── api_test.py        # API endpoint testing
│   ├── quick_test.sh      # Quick validation tests
│   ├── startup_test.sh    # Service startup tests
│   ├── integration_test.sh # Original integration tests
│   └── integration_test_new.sh # Enhanced integration tests
├── build/                 # Build and compilation tests
│   └── build_test.sh      # Docker build validation
├── health/                # Health and monitoring tests
│   ├── health-check.sh    # Service health checks
│   └── test_network.sh    # Network connectivity tests
└── unit/                  # Unit tests (to be added)
    └── (future unit tests)
```

## Test Categories

### 🔧 Integration Tests (`./integration/`)
- **api_test.py**: Python-based API endpoint testing
- **quick_test.sh**: Fast configuration and syntax validation
- **startup_test.sh**: Service startup and initialization testing
- **integration_test.sh**: Original comprehensive integration tests
- **integration_test_new.sh**: Enhanced integration test suite

### 🏗️ Build Tests (`./build/`)
- **build_test.sh**: Docker container build validation for all services

### 🩺 Health Tests (`./health/`)
- **health-check.sh**: Service health monitoring and status checks
- **test_network.sh**: Network connectivity and port availability tests

### 🧩 Unit Tests (`./unit/`)
- **spellbook/**: Complete backend unit test suite for the Commander Spellbook application
- **spellbook-client/**: Python client library unit tests
- **website/**: Website component unit tests  
- **common/**: Shared utility and common module unit tests

## Quick Start

### Run All Tests
```bash
# From the project root
./tests/run_all_tests.sh
```

### Run Specific Test Categories
```bash
# Integration tests only
./tests/integration/quick_test.sh

# Build tests only
./tests/build/build_test.sh

# Health tests only
./tests/health/health-check.sh
```

## Test Dependencies

### Required for Python Tests
- Python 3.8+
- requests library: `pip install requests`

### Required for Shell Tests
- Docker and Docker Compose
- curl (for API testing)
- netstat or ss (for network testing)

## Test Results

Test results and logs are typically saved to:
- `/tmp/` directory for build logs
- Console output for validation results
- `../TEST_RESULTS.md` for comprehensive test reports

## Adding New Tests

### Integration Tests
Add new integration tests to `./integration/` directory. Follow the pattern:
```bash
#!/bin/bash
# Test description
# Include color coding and result tracking
```

### Unit Tests
Add service-specific unit tests to `./unit/` directory organized by component:
```bash
./unit/
├── spellbook/
│   ├── pytest.ini         # Pytest configuration
│   ├── test_commands.py    # Management command tests
│   ├── test_validators.py  # Input validation tests
│   ├── test_models/        # Database model tests
│   ├── test_views/         # API view tests
│   └── test_admin/         # Admin interface tests
├── spellbook-client/
│   ├── pytest.ini         # Client pytest configuration
│   ├── test_*.py          # Client library tests
│   └── testing.py         # Testing utilities
├── website/
│   └── tests.py           # Website component tests
└── common/
    ├── test_markdown.py    # Markdown processing tests
    └── test_itertools.py   # Utility function tests
```

### Build Tests
Add new build validations to `./build/` directory for additional services.

## Environment Requirements

Tests expect the following environment:
- Docker daemon running
- Project secrets generated (`./setup-secrets.sh`)
- Environment variables configured (`.env` file)
- SSL certificates generated (`./generate-ssl-certs.sh`)

## Troubleshooting

### Common Issues
1. **Permission denied**: Ensure test scripts are executable (`chmod +x test_file.sh`)
2. **Docker not found**: Ensure Docker is installed and daemon is running
3. **Port conflicts**: Check for services running on required ports
4. **Missing secrets**: Run `./setup-secrets.sh` from project root

### Debug Mode
Most test scripts support verbose output. Check individual script documentation for debug flags.

## Continuous Integration

These tests are designed to be CI/CD friendly and can be integrated into:
- GitHub Actions
- GitLab CI
- Jenkins pipelines
- Local development workflows

## Contributing

When adding new tests:
1. Place in appropriate category directory
2. Follow existing naming conventions
3. Include proper error handling and output formatting
4. Update this README with new test descriptions
5. Ensure tests are idempotent (can be run multiple times)

---

**Last Updated**: June 20, 2025  
**Test Coverage**: Configuration, Build, Integration, Health Monitoring
