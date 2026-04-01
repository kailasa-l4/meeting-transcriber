"""Gold Lead Research System - AgentOS Entry Point."""
from src.config import settings

# Minimal entry point — agents, teams, and workflows will be registered in Phase 1
print(f"Gold Lead Research System starting on {settings.agno_api_url}")
print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
print(f"CORS origins: {settings.cors_origins}")
