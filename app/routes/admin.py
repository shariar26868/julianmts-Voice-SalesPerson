from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.config.database import get_methodology_prompt_collection, get_system_config_collection
from app.utils.helpers import current_timestamp, build_api_response

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Default prompts seeded on first fetch
DEFAULT_PROMPTS = {
    "MEDDIC": """The salesperson is using the MEDDIC sales methodology.
As a representative, challenge them on each pillar:
- Metrics: Demand specific ROI numbers and measurable outcomes. Don't accept vague claims.
- Economic Buyer: Question whether the right decision maker is present.
- Decision Criteria: Push them to understand your exact evaluation criteria.
- Decision Process: Ask about internal approval steps and stakeholders.
- Identify Pain: Make them work hard to uncover your real pain points — don't volunteer them.
- Champion: Be skeptical. They need to earn your trust before you advocate for them internally.""",

    "BANT": """The salesperson is using the BANT sales methodology.
As a representative, make them qualify properly:
- Budget: Be vague and non-committal about budget. Don't reveal numbers easily.
- Authority: Question whether you have final sign-off or need others involved.
- Need: Force them to discover your needs through smart questions, don't hand them over.
- Timeline: Be non-committal about decision timelines. Show competing priorities.""",

    "CHALLENGER_SALES": """The salesperson may use the Challenger Sales approach — teaching, tailoring, and taking control.
As a representative:
- Push back when they challenge your assumptions or reframe your thinking.
- Sometimes agree with their insights, sometimes resist — be realistic.
- React with mild defensiveness if they imply you've been doing things wrong.
- Reward them if they bring genuinely new perspectives with data.""",

    "SPIN_SELLING": """The salesperson is using SPIN Selling methodology.
As a representative, respond naturally to their question types:
- Situation questions: Answer briefly, don't over-share.
- Problem questions: Acknowledge pain points but downplay urgency initially.
- Implication questions: Show concern when they highlight consequences of inaction.
- Need-payoff questions: Engage positively when they connect solutions to your needs.""",

    "MEDDPICC": """The salesperson is using MEDDPICC methodology.
As a representative, challenge them on all pillars:
- Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion (same as MEDDIC)
- Paper Process: Bring up legal, procurement, and contract complexity as obstacles.
- Competition: Hint that you are evaluating other vendors. Don't make it easy.""",

    "VALUE_SELLING": """The salesperson is using Value Selling methodology.
As a representative:
- Focus conversations on business outcomes and value, not features.
- Challenge them to quantify the value they claim to deliver.
- Ask how their solution compares to your current process in dollar terms.
- Be skeptical of generic value claims — demand specifics relevant to your business.""",
}


class MethodologyPromptUpdate(BaseModel):
    prompt: str
    description: Optional[str] = None


async def _seed_defaults():
    """Insert default prompts if collection is empty."""
    col = get_methodology_prompt_collection()
    for name, prompt in DEFAULT_PROMPTS.items():
        existing = await col.find_one({"_id": name})
        if not existing:
            await col.insert_one({
                "_id": name,
                "name": name,
                "prompt": prompt,
                "description": f"Default prompt for {name} methodology",
                "updated_at": current_timestamp()
            })


@router.get("/methodology-prompts", response_model=dict)
async def get_all_methodology_prompts():
    """Get all sales methodology prompts"""
    await _seed_defaults()
    col = get_methodology_prompt_collection()
    prompts = []
    async for doc in col.find():
        doc["id"] = str(doc.pop("_id"))
        prompts.append(doc)
    return build_api_response(success=True, data={"prompts": prompts})


@router.get("/methodology-prompts/{methodology_name}", response_model=dict)
async def get_methodology_prompt(methodology_name: str):
    """Get prompt for a specific methodology"""
    await _seed_defaults()
    col = get_methodology_prompt_collection()
    doc = await col.find_one({"_id": methodology_name.upper()})
    if not doc:
        raise HTTPException(status_code=404, detail="Methodology not found")
    doc["id"] = str(doc.pop("_id"))
    return build_api_response(success=True, data=doc)


@router.put("/methodology-prompts/{methodology_name}", response_model=dict)
async def update_methodology_prompt(methodology_name: str, body: MethodologyPromptUpdate):
    """Update prompt for a specific methodology"""
    await _seed_defaults()
    col = get_methodology_prompt_collection()
    key = methodology_name.upper()
    existing = await col.find_one({"_id": key})
    if not existing:
        raise HTTPException(status_code=404, detail="Methodology not found")

    update = {"prompt": body.prompt, "updated_at": current_timestamp()}
    if body.description:
        update["description"] = body.description

    await col.update_one({"_id": key}, {"$set": update})
    return build_api_response(success=True, message=f"{key} prompt updated successfully")


# ─────────────────────────────────────────────
# Global Admin System Prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT_DOC_ID = "global_system_prompt"


class SystemPromptUpdate(BaseModel):
    prompt: str


@router.get("/system-prompt", response_model=dict)
async def get_system_prompt():
    """Get the current global admin system prompt."""
    col = get_system_config_collection()
    doc = await col.find_one({"_id": SYSTEM_PROMPT_DOC_ID})
    if not doc:
        return build_api_response(
            success=True,
            data={"prompt": None, "is_default": True, "updated_at": None},
            message="No custom prompt set — using built-in default"
        )
    return build_api_response(
        success=True,
        data={
            "prompt": doc["prompt"],
            "is_default": False,
            "updated_at": doc.get("updated_at")
        }
    )


@router.put("/system-prompt", response_model=dict)
async def set_system_prompt(body: SystemPromptUpdate):
    """Set (or replace) the global admin system prompt."""
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    col = get_system_config_collection()
    await col.update_one(
        {"_id": SYSTEM_PROMPT_DOC_ID},
        {"$set": {"prompt": body.prompt.strip(), "updated_at": current_timestamp()}},
        upsert=True
    )
    return build_api_response(success=True, message="Global system prompt updated successfully")


@router.delete("/system-prompt", response_model=dict)
async def delete_system_prompt():
    """Delete the admin system prompt — AI reverts to built-in default + methodology."""
    col = get_system_config_collection()
    await col.delete_one({"_id": SYSTEM_PROMPT_DOC_ID})
    return build_api_response(success=True, message="Custom prompt deleted — reverted to built-in default")
