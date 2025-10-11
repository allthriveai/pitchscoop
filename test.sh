#!/bin/bash
# Quick onboarding test runner

echo "🧪 Running onboarding tests..."
docker compose exec api python test_onboarding.py
