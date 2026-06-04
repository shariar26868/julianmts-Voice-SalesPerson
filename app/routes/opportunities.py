"""
Manual Opportunities API
------------------------
User নিজে manually opportunity data input করতে পারবে।
AI-generated opportunities-এর সাথে কোনো সম্পর্ক নেই।

Same fields as AI-generated:
  - name       : opportunity name
  - value      : e.g. "$125,000"
  - stage      : "Discovery" | "Proposal" | "Negotiation" | "Closed Won" | "Closed Lost"
  - close_date : e.g. "Mar 15, 2025"
  - probability: 0-100

Endpoints:
  POST   /api/opportunities/                          — Create opportunity
  GET    /api/opportunities/company/{company_id}      — List all for a company
  GET    /api/opportunities/{opportunity_id}          — Get single opportunity
  PUT    /api/opportunities/{opportunity_id}          — Update opportunity
  DELETE /api/opportunities/{opportunity_id}          — Delete opportunity
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel, Field
from app.config.database import get_opportunities_collection
from app.utils.helpers import generate_id, current_timestamp, build_api_response

router = APIRouter(tags=["Opportunities"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────

STAGE_OPTIONS = ["Discovery", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]


class OpportunityCreate(BaseModel):
    company_id: str = Field(..., description="The company this opportunity belongs to")
    name: str = Field(..., description="Opportunity name, e.g. 'Enterprise License Upgrade'")
    value: str = Field(..., description="Deal value, e.g. '$125,000'")
    stage: str = Field(
        ...,
        description=f"Current stage. Options: {', '.join(STAGE_OPTIONS)}"
    )
    close_date: str = Field(..., description="Expected close date, e.g. 'Mar 15, 2025'")
    probability: int = Field(
        ..., ge=0, le=100,
        description="Win probability 0–100"
    )


class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None
    stage: Optional[str] = None
    close_date: Optional[str] = None
    probability: Optional[int] = Field(None, ge=0, le=100)


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/", response_model=dict)
async def create_opportunity(body: OpportunityCreate):
    """
    Create a new opportunity manually.

    Body example:
    {
      "company_id": "abc123",
      "name": "Enterprise License Upgrade",
      "value": "$125,000",
      "stage": "Negotiation",
      "close_date": "Mar 15, 2025",
      "probability": 75
    }
    """
    col = get_opportunities_collection()

    # Validate stage
    if body.stage not in STAGE_OPTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage '{body.stage}'. Must be one of: {', '.join(STAGE_OPTIONS)}"
        )

    now = current_timestamp()
    opp_id = generate_id()

    doc = {
        "_id":         opp_id,
        "company_id":  body.company_id,
        "name":        body.name.strip(),
        "value":       body.value.strip(),
        "stage":       body.stage,
        "close_date":  body.close_date.strip(),
        "probability": body.probability,
        "created_at":  now,
        "updated_at":  now,
    }

    await col.insert_one(doc)

    doc["id"] = str(doc.pop("_id"))
    return build_api_response(
        success=True,
        data=doc,
        message="Opportunity created successfully"
    )


@router.get("/company/{company_id}", response_model=dict)
async def list_opportunities(company_id: str):
    """
    List all opportunities for a specific company.
    Returns the same field structure as the AI-generated opportunities.

    Example: GET /api/opportunities/company/abc123
    """
    col = get_opportunities_collection()

    opportunities = []
    async for doc in col.find({"company_id": company_id}, sort=[("created_at", -1)]):
        doc["id"] = str(doc.pop("_id"))
        opportunities.append(doc)

    return build_api_response(
        success=True,
        data={
            "company_id":    company_id,
            "opportunities": opportunities,
            "total":         len(opportunities),
        },
        message=f"{len(opportunities)} opportunities found"
    )


@router.get("/{opportunity_id}", response_model=dict)
async def get_opportunity(opportunity_id: str):
    """Get a single opportunity by its ID."""
    col = get_opportunities_collection()

    doc = await col.find_one({"_id": opportunity_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    doc["id"] = str(doc.pop("_id"))
    return build_api_response(success=True, data=doc)


@router.put("/{opportunity_id}", response_model=dict)
async def update_opportunity(opportunity_id: str, body: OpportunityUpdate):
    """
    Update an existing opportunity.
    Only send the fields you want to change — all fields are optional.

    Body example (partial update):
    {
      "stage": "Closed Won",
      "probability": 100
    }
    """
    col = get_opportunities_collection()

    existing = await col.find_one({"_id": opportunity_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Build update payload — only include provided fields
    update_data: dict = {"updated_at": current_timestamp()}

    if body.name is not None:
        update_data["name"] = body.name.strip()
    if body.value is not None:
        update_data["value"] = body.value.strip()
    if body.stage is not None:
        if body.stage not in STAGE_OPTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage '{body.stage}'. Must be one of: {', '.join(STAGE_OPTIONS)}"
            )
        update_data["stage"] = body.stage
    if body.close_date is not None:
        update_data["close_date"] = body.close_date.strip()
    if body.probability is not None:
        update_data["probability"] = body.probability

    await col.update_one({"_id": opportunity_id}, {"$set": update_data})

    updated = await col.find_one({"_id": opportunity_id})
    updated["id"] = str(updated.pop("_id"))

    return build_api_response(
        success=True,
        data=updated,
        message="Opportunity updated successfully"
    )


@router.delete("/{opportunity_id}", response_model=dict)
async def delete_opportunity(opportunity_id: str):
    """Delete an opportunity by ID."""
    col = get_opportunities_collection()

    existing = await col.find_one({"_id": opportunity_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    await col.delete_one({"_id": opportunity_id})

    return build_api_response(
        success=True,
        message=f"Opportunity '{existing.get('name')}' deleted successfully"
    )
