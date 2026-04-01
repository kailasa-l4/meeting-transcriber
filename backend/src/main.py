"""Gold Lead Research System -- FastAPI application with AgentOS integration.

Start with:
    uv run python -m src.main
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    db_host = settings.database_url.split("@")[1] if "@" in settings.database_url else "configured"
    print(f"Gold Lead Research System v0.1.0")
    print(f"  Database: {db_host}")
    print(f"  CORS origins: {settings.cors_origins}")
    print(f"  Routes: {len(application.routes)}")
    yield


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Gold Lead Research System",
    version="0.1.0",
    description="Automated gold lead discovery, verification, and outreach pipeline",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Custom API routers
# ---------------------------------------------------------------------------

from src.api.country_jobs import router as jobs_router  # noqa: E402
from src.api.leads import router as leads_router  # noqa: E402
from src.api.approvals import router as approvals_router  # noqa: E402
from src.api.metrics import router as metrics_router  # noqa: E402

app.include_router(jobs_router)
app.include_router(leads_router)
app.include_router(approvals_router)
app.include_router(metrics_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "version": "0.1.0"}


# ---------------------------------------------------------------------------
# Agno agent/team/workflow registration
#
# These are registered so that the Agno Playground UI (if used) can
# discover and interact with them. They are also importable directly.
# ---------------------------------------------------------------------------

def get_agents():
    """Lazy import all agents to avoid circular imports at module level."""
    from src.agents.discovery.miner_finder import miner_finder_agent
    from src.agents.discovery.broker_finder import broker_finder_agent
    from src.agents.discovery.exporter_finder import exporter_finder_agent
    from src.agents.discovery.directory_scanner import directory_scanner_agent
    from src.agents.discovery.contact_extractor import contact_extractor_agent
    from src.agents.verification.entity_verifier import entity_verifier_agent
    from src.agents.verification.contact_verifier import contact_verifier_agent
    from src.agents.verification.source_quality_verifier import source_quality_verifier_agent
    from src.agents.verification.duplicate_resolver import duplicate_resolver_agent
    from src.agents.outreach.outreach_agent import outreach_agent

    return [
        miner_finder_agent,
        broker_finder_agent,
        exporter_finder_agent,
        directory_scanner_agent,
        contact_extractor_agent,
        entity_verifier_agent,
        contact_verifier_agent,
        source_quality_verifier_agent,
        duplicate_resolver_agent,
        outreach_agent,
    ]


def get_teams():
    """Lazy import teams."""
    from src.teams.discovery_team import discovery_team
    from src.teams.verification_team import verification_team

    return [discovery_team, verification_team]


def get_workflows():
    """Lazy import workflows."""
    from src.workflows.country_workflow import country_research_workflow

    return [country_research_workflow]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
