# Docker Environment Variables Troubleshooting

**Issue**: Docker restart not picking up all keys from `.env` file

**Date Fixed**: 2025-09-19

## 🔍 Problem Diagnosis

### Symptoms:
- Docker warnings about missing environment variables
- Variables showing as empty strings in `docker compose config`
- Application errors due to missing configuration

### Root Cause:
Missing environment variables in `.env` file that were referenced in `docker-compose.yml`

## 🛠️ What Was Wrong

### Missing Variables in `.env`:
1. `SYSTEM_LLM_AZURE_EMBEDDING_DEPLOYMENT` - Referenced in docker-compose.yml but missing from .env
2. `BRIGHT_DATA_BASE_URL` - Referenced in docker-compose.yml but missing from .env  
3. `BRIGHT_DATA_RATE_LIMIT` - Referenced in docker-compose.yml but missing from .env

### Docker Compose Warnings:
```bash
WARN[0000] The "SYSTEM_LLM_AZURE_EMBEDDING_DEPLOYMENT" variable is not set. Defaulting to a blank string.
WARN[0000] The "BRIGHT_DATA_BASE_URL" variable is not set. Defaulting to a blank string. 
WARN[0000] The "BRIGHT_DATA_RATE_LIMIT" variable is not set. Defaulting to a blank string.
```

## ✅ Solution Applied

### Added Missing Variables to `.env`:
```bash
# Azure OpenAI Embedding Model
SYSTEM_LLM_AZURE_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# BrightData Configuration  
BRIGHT_DATA_BASE_URL=https://brightdata.com/api/v1
BRIGHT_DATA_RATE_LIMIT=100
```

### Verification Steps:
1. **Check docker-compose config**: `docker compose config` - no more warnings
2. **Verify environment in container**: All variables now properly loaded
3. **Test application**: Environment variables accessible in Python code

## 🔧 How to Debug Environment Variable Issues

### 1. Check Docker Compose Configuration:
```bash
# See resolved environment variables
docker compose config

# Filter specific variables
docker compose config | grep -E "(VARIABLE_PATTERN)"
```

### 2. Check Variables Inside Container:
```bash
# List all environment variables
docker compose exec api env

# Check specific variables
docker compose exec api env | grep SYSTEM_LLM_AZURE
```

### 3. Test in Python:
```bash
docker compose exec api python -c "
import os
vars_to_check = ['VAR1', 'VAR2'] 
for var in vars_to_check:
    print(f'{var}: {os.getenv(var)}')
"
```

## 📋 Best Practices Going Forward

### 1. Environment Variable Management:
- **Always validate**: Run `docker compose config` after changes
- **Keep .env in sync**: Ensure all variables referenced in docker-compose.yml exist in .env
- **Use meaningful defaults**: Consider setting default values in docker-compose.yml for optional variables

### 2. Docker Compose Patterns:
```yaml
# Option 1: Required variable (will warn if missing)
environment:
  - REQUIRED_VAR=${REQUIRED_VAR}

# Option 2: Optional variable with default
environment:
  - OPTIONAL_VAR=${OPTIONAL_VAR:-default_value}
```

### 3. Testing After Changes:
```bash
# Full restart and test sequence
docker compose down
docker compose config  # Check for warnings
docker compose up -d
docker compose exec api env | grep YOUR_VARS
```

## 📊 Current Status

### ✅ All Environment Variables Loading:
- `SYSTEM_LLM_AZURE_*` - All 5 variables loaded
- `BRIGHT_DATA_*` - All 3 variables loaded  
- `GLADIA_*` - Both variables loaded
- `REDIS_URL` - Loaded
- `MINIO_*` - All 4 variables loaded

### 🎯 Verified Working:
- Docker containers start without warnings
- Environment variables accessible in application code
- All services connecting properly

## 🚨 Common Pitfalls to Avoid

1. **Referencing undefined variables**: Always add to .env if used in docker-compose.yml
2. **Forgetting restart**: Changes to .env require container restart
3. **Case sensitivity**: Environment variable names are case-sensitive
4. **Whitespace issues**: No spaces around = in .env file
5. **Quote handling**: Be careful with quotes in .env values

## 🔄 Recovery Process

If environment variables stop working again:

1. **Check .env file**: Ensure all referenced variables exist
2. **Validate syntax**: No extra spaces, proper format
3. **Test config**: Run `docker compose config` for warnings
4. **Full restart**: `docker compose down && docker compose up -d`
5. **Verify loading**: Test variables inside container

---

**Last Updated**: 2025-09-19  
**Status**: ✅ Resolved - All environment variables loading correctly