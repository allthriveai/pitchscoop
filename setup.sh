#!/bin/bash

# PitchScoop Setup Script for New Team Members
# This script sets up the development environment automatically

set -e  # Exit on any error

echo "🚀 Setting up PitchScoop development environment..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔧 Building and starting services..."
echo "   This may take a few minutes on first run..."

# Start services
docker compose up --build -d

# Wait a moment for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Test if API is responding
echo "🧪 Testing API health..."
if curl -s localhost:8000/api/healthz | grep -q "ok"; then
    echo "✅ API is healthy!"
else
    echo "⚠️  API might still be starting up..."
    echo "   Check with: docker compose logs api"
fi

echo ""
echo "🎉 Setup complete! Your PitchScoop development environment is ready."
echo ""
echo "📋 Quick access:"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • MinIO Console: http://localhost:9001"
echo "     (user: pitchscoop, password: pitchscoop123)"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs: docker compose logs -f api"
echo "   • Run tests: docker compose exec api pytest tests/"
echo "   • Stop services: docker compose down"
echo ""
echo "📚 Need help? Check README.md or WARP.md for detailed docs."