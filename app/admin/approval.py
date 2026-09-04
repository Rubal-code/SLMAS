from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/admin", tags=["admin"])


class ApprovalRequest(BaseModel):
    action: str = Field(..., min_length=1)
    approved: bool = Field(...)
    reason: Optional[str] = None


approved_actions: Dict[str, bool] = {}


@router.post("/approve")
async def approve_action(payload: ApprovalRequest):
    approved_actions[payload.action] = payload.approved
    return {
        "action": payload.action,
        "approved": payload.approved,
        "reason": payload.reason,
        "status": "saved",
    }


@router.get("/approve/{action}")
async def get_approval(action: str):
    return {"action": action, "approved": approved_actions.get(action, False)}
