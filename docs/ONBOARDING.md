# 🎯 New Team Member Onboarding Checklist

Welcome to PitchScoop! Follow this checklist to get up and running quickly.

## ✅ Prerequisites (5 minutes)

- [ ] **Install Docker Desktop**
  - Download from: https://docs.docker.com/get-docker/
  - Make sure it's running (Docker icon in system tray)

- [ ] **Install Git** (if not already installed)
  - macOS: `brew install git` or download from git-scm.com
  - Windows: Download from git-scm.com
  - Linux: `sudo apt install git` or equivalent

- [ ] **Clone the Repository**
  ```bash
  git clone <repository-url>
  cd pitchscoop
  ```

## 🚀 Quick Setup (2 minutes)

Choose one of these methods:

### Option 1: Automated Setup (Recommended)
```bash
./setup.sh
```

### Option 2: Manual Setup
```bash
cp .env.example .env
docker compose up --build
```

## 🧪 Verification (2 minutes)

After setup, verify everything is working:

- [ ] **API Health Check**
  ```bash
  curl localhost:8000/api/healthz
  # Should return: {"ok": true}
  ```

- [ ] **Open API Documentation**
  - Visit: http://localhost:8000/docs
  - You should see the FastAPI Swagger interface

- [ ] **Check MinIO Console**
  - Visit: http://localhost:9001
  - Login: `pitchscoop` / `pitchscoop123`
  - You should see the MinIO admin interface

- [ ] **Run Tests**
  ```bash
  docker compose exec api pytest tests/
  # Should pass all tests
  ```

## 🎯 Key Resources

- [ ] **Bookmark These URLs**
  - API: http://localhost:8000
  - API Docs: http://localhost:8000/docs
  - MinIO Console: http://localhost:9001

- [ ] **Read Key Documentation**
  - [ ] `README.md` - Project overview and setup
  - [ ] `WARP.md` - Detailed development guidelines
  - [ ] `api/domains/` - Explore the domain structure

- [ ] **Understand the Architecture**
  - [ ] Review the event-driven workflow in README.md
  - [ ] Look at the MCP tools available
  - [ ] Understand multi-tenant design (everything scoped by `event_id`)

## 🔧 Development Workflow

- [ ] **Learn Key Commands**
  ```bash
  # Start services
  docker compose up --build
  
  # View API logs
  docker compose logs -f api
  
  # Run tests
  docker compose exec api pytest tests/
  
  # Stop services
  docker compose down
  ```

- [ ] **Test API Endpoints**
  - Use the Swagger UI at http://localhost:8000/docs
  - Try creating an event, starting a recording, and scoring a pitch

## 🎪 Optional: Enable AI Features

If you want to test the full AI-powered features:

- [ ] **Get Azure OpenAI Access** (optional)
  - Ask team lead for credentials
  - Update your `.env` file:
    ```bash
    SYSTEM_LLM_AZURE_ENDPOINT=https://your-resource.openai.azure.com/
    SYSTEM_LLM_AZURE_API_KEY=your_key_here
    SYSTEM_LLM_AZURE_DEPLOYMENT=your_deployment_name
    ```

- [ ] **Get Gladia API Key** (optional for STT)
  - Sign up at https://gladia.io
  - Update your `.env` file:
    ```bash
    GLADIA_API_KEY=your_gladia_key_here
    ```

## 🆘 Troubleshooting

**API not starting?**
```bash
docker compose logs api
```

**Port conflicts?**
```bash
# Check what's using the ports
lsof -i :8000  # API
lsof -i :6379  # Redis
lsof -i :9000  # MinIO
```

**Docker issues?**
```bash
# Clean restart
docker compose down -v
docker compose up --build
```

## 🤝 Getting Help

- [ ] **Join Team Communication** (Slack, Discord, etc.)
- [ ] **Ask Questions** - Don't hesitate!
- [ ] **Check Documentation** - README.md and WARP.md have lots of details

## ✅ Ready to Code!

Once you've completed this checklist:

1. **Explore the codebase** in `api/domains/`
2. **Try the MCP tools** via the API docs
3. **Run the test suite** to understand expected behavior
4. **Pick your first task** from the project board

**Welcome to the team! 🎉**

---

*Estimated setup time: ~10 minutes*  
*If you get stuck, ask for help - we're here to support you!*