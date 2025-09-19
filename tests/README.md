# PitchScoop Tests

This directory contains all tests for the PitchScoop project, organized by category and type.

## Directory Structure

```
tests/
├── mcp/                    # MCP protocol and server tests
│   ├── mcp_server_test.py  # MCP server implementation test
│   ├── test_mcp_*.py      # MCP protocol tests
│   └── ...
├── integration/            # Integration tests with external services
│   ├── test_azure_integration.py
│   ├── test_market_integration.py
│   ├── test_redis_vector_integration.py
│   └── ...
├── unit/                   # Unit tests for individual components
│   ├── test_*.py          # Component unit tests
│   └── domains/           # Domain-specific unit tests
│       ├── recordings/
│       └── scoring/
├── e2e/                    # End-to-end workflow tests
│   ├── test_complete_recording_flow.py
│   ├── test_recording_flow_*.py
│   └── ...
├── tools/                  # Testing tools and utilities
│   ├── simple_test_server.py
│   ├── web_test_server.py
│   └── demo_llm.py
├── fixtures/               # Test data and fixtures
│   └── audio_samples/
├── mocks/                  # Mock implementations
└── conftest.py            # Pytest configuration
```

## Running Tests

### Using the Test Runner

```bash
# Run all tests
python run_tests.py all

# Run specific category
python run_tests.py unit
python run_tests.py integration
python run_tests.py mcp
python run_tests.py e2e

# Run with options
python run_tests.py unit -v --fail-fast
python run_tests.py integration --docker
```

### Using Pytest Directly

```bash
# From project root
PYTHONPATH=.:api python -m pytest tests/

# Specific categories
PYTHONPATH=.:api python -m pytest tests/unit/
PYTHONPATH=.:api python -m pytest tests/mcp/
PYTHONPATH=.:api python -m pytest tests/integration/
```

### Using Docker

```bash
# Run tests inside Docker container
docker compose exec api python -m pytest tests/
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual components in isolation
- Fast execution, no external dependencies
- Mock external services and APIs
- Test business logic and domain entities

### Integration Tests (`tests/integration/`)
- Test integration with external services
- May require API keys or external resources
- Test Redis, Azure OpenAI, Gladia API integration
- Slower execution due to network calls

### MCP Tests (`tests/mcp/`)
- Test MCP protocol implementation
- Test MCP server functionality
- Test tool registration and execution
- Test Claude Desktop integration

### End-to-End Tests (`tests/e2e/`)
- Test complete workflows and user scenarios
- Test full pitch recording and scoring flow
- May require multiple services running
- Comprehensive validation of system behavior

### Tools (`tests/tools/`)
- Testing utilities and helper tools
- Test servers for manual testing
- Development and debugging tools

## Test Markers

Tests can be marked with pytest markers:

```python
import pytest

@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration_function():
    pass

@pytest.mark.slow
def test_slow_function():
    pass

@pytest.mark.requires_api_key
def test_with_api_key():
    pass
```

Run specific markers:
```bash
PYTHONPATH=.:api python -m pytest -m unit tests/
PYTHONPATH=.:api python -m pytest -m "not slow" tests/
```

## Import Guidelines

All test files use this import pattern to access the main codebase:

```python
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

# Now you can import from domains, etc.
from domains.events.mcp.events_mcp_tools import EVENTS_MCP_TOOLS
```

## Configuration

- `pytest.ini` - Pytest configuration
- `conftest.py` - Shared fixtures and test configuration
- `fixtures/` - Test data and sample files
- `mocks/` - Mock implementations of external services

## Best Practices

1. **Organize by category** - Put tests in the right directory
2. **Use descriptive names** - `test_create_event_with_valid_data()`
3. **Keep tests focused** - One concept per test
4. **Use fixtures** - Share common setup code
5. **Mock externally** - Don't depend on external services in unit tests
6. **Mark appropriately** - Use pytest markers for organization
7. **Document complex tests** - Add docstrings explaining the test scenario

## Common Issues

### Import Errors
If you get import errors, ensure:
1. You're running from the project root directory
2. PYTHONPATH includes both `.` and `api`
3. The import path setup is at the top of your test file

### Missing Dependencies
Some tests require external services or API keys:
- Integration tests need Redis, MinIO, etc.
- MCP tests need the `mcp` Python package
- Run `pip install -r api/requirements.txt` for all dependencies

### Docker Tests
To run tests in Docker (where all dependencies are available):
```bash
docker compose up -d
docker compose exec api python -m pytest tests/category/
```