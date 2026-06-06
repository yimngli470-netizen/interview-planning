from fastapi import APIRouter

from .. import llm

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
def ai_status():
    """Whether AI auto-fill is available (ANTHROPIC_API_KEY is set)."""
    return {"configured": llm.ai_configured()}
