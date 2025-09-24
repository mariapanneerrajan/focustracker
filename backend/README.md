# Focus Tracker Backend - Phase 1 ✅

A FastAPI backend application for the Focus Tracker project, built following SOLID principles and clean architecture.

## 🏗 Architecture

The backend follows clean architecture with clear separation of concerns:

```
backend/
├── app/
│   ├── api/                 # API routes/controllers
│   ├── core/                # Core configuration
│   ├── domain/              # Domain models (future)
│   ├── services/            # Business logic services (future)
│   ├── repositories/        # Repository interfaces (future)
│   ├── adapters/            # Third-party service adapters (future)
│   ├── utils/               # Utility functions (future)
│   └── tests/               # Test files
├── requirements.txt         # Python dependencies
├── pytest.ini             # Pytest configuration
└── env.example            # Environment variables template
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests:**
   ```bash
   python run_tests.py
   # or
   python -m pytest app/tests/ -v
   ```

4. **Start the development server:**
   ```bash
   python start_server.py
   # or
   python -m app.main
   ```

## 📚 API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health
- **Detailed Health**: http://127.0.0.1:8000/health/detailed

## 🧪 Testing

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Tests
```bash
python -m pytest app/tests/test_health.py -v
```

### Test Coverage
```bash
python -m pytest app/tests/ --cov=app
```

## 🏥 Health Endpoints

### GET /health
Basic health check endpoint that returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-24T18:23:15.308328",
  "version": "1.0.0",
  "environment": "development"
}
```

### GET /health/detailed
Detailed health information including system status:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-24T18:23:23.261875",
  "version": "1.0.0",
  "environment": "development",
  "debug": true,
  "system": {
    "api_version": "/api/v1",
    "project_name": "Focus Tracker"
  },
  "services": {
    "database": "not_configured",
    "authentication": "not_configured"
  }
}
```

## 🔧 Configuration

Copy `env.example` to `.env` and customize:

```env
ENVIRONMENT=development
DEBUG=true
HOST=127.0.0.1
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 📋 SOLID Principles Implementation

This Phase 1 implementation demonstrates:

1. **Single Responsibility**: Each module has one clear purpose
   - `main.py`: Application factory and configuration
   - `config.py`: Configuration management only
   - `health.py`: Health check endpoints only

2. **Open/Closed**: Code is open for extension, closed for modification
   - Router pattern allows adding new endpoints without modifying existing code
   - Configuration system can be extended with new settings

3. **Liskov Substitution**: Ready for interface implementations in future phases
   - Service interfaces will be interchangeable

4. **Interface Segregation**: Small, focused interfaces
   - Health endpoints provide only necessary information
   - Configuration class only includes relevant settings

5. **Dependency Inversion**: Foundation for future abstraction
   - Factory pattern for app creation
   - Ready for dependency injection container

## 🔄 Next Phases

Phase 1 provides the foundation for:
- **Phase 2**: Database setup with Firebase/service abstraction
- **Phase 3**: Authentication system with JWT
- **Phase 4**: Session management API
- **Phase 5**: Analytics and statistics

## ✅ Phase 1 Validation

**Test Command**: Access http://127.0.0.1:8000/docs to verify:
- ✅ Working FastAPI server with health endpoints
- ✅ Automatic API documentation (Swagger/OpenAPI)
- ✅ 11/11 tests passing
- ✅ Clean architecture foundation
- ✅ CORS configuration for frontend integration
- ✅ Environment-based configuration
- ✅ Test-driven development setup
