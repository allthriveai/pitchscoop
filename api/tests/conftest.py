"""
Pytest configuration and shared fixtures for PitchScoop tests.
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def gladia_api_key():
    """Get Gladia API key from environment for integration tests."""
    import os
    api_key = os.getenv("GLADIA_API_KEY")
    if not api_key:
        pytest.skip("GLADIA_API_KEY not set - skipping integration test")
    return api_key