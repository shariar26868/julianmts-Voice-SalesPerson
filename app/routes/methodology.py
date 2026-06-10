"""
Sales Methodology Management API
---------------------------------
Endpoints:
  GET  /                  — list all methodologies with their core fields
  GET  /{name}            — get a specific methodology by name (case-insensitive)
  POST /                  — create (or update) a methodology with name + core_fields
  DELETE /{name}          — delete a custom methodology (defaults cannot be deleted)
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.schemas import SalesMethodologyCreate, CoreField
from app.config.database import get_sales_methodology_collection
from app.utils.helpers import current_timestamp, build_api_response

# router = APIRouter(tags=["Methodology"])
router = APIRouter(prefix="/api/methodology", tags=["Methodology"])

# ─────────────────────────────────────────────────────────────────────────────
# Default methodologies (pre-seeded from the screenshots)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_METHODOLOGIES = {
    "Value Selling": [
        {"field": "Business Value",    "definition": "Measurable customer gain"},
        {"field": "ROI",               "definition": "Financial return expected"},
        {"field": "Customer Goals",    "definition": "Strategic objectives"},
        {"field": "Pain Cost",         "definition": "Cost of current problem"},
        {"field": "Success Outcomes",  "definition": "Desired measurable result"},
    ],
    "MEDDIC": [
        {"field": "Metrics",           "definition": "Quantified business impact / ROI"},
        {"field": "Economic Buyer",    "definition": "Person with final budget authority"},
        {"field": "Decision Criteria", "definition": "Factors used to evaluate vendors"},
        {"field": "Decision Process",  "definition": "Steps to approve purchase"},
        {"field": "Identify Pain",     "definition": "Main business problem to solve"},
        {"field": "Champion",          "definition": "Internal advocate pushing your deal"},
    ],
    "Challenger Sales": [
        {"field": "Commercial Insight",     "definition": "New perspective taught to buyer"},
        {"field": "Pain Intensity",         "definition": "Severity of business issue"},
        {"field": "Change Urgency",         "definition": "Need to act now"},
        {"field": "Stakeholder Alignment",  "definition": "Internal agreement across teams"},
        {"field": "Status Quo Cost",        "definition": "Risk/cost of doing nothing"},
    ],
    "BANT": [
        {"field": "Budget",    "definition": "Available spending capacity"},
        {"field": "Authority", "definition": "Decision-maker ownership"},
        {"field": "Need",      "definition": "Clear business requirement"},
        {"field": "Timeline",  "definition": "Expected buying timeframe"},
    ],
    "SPIN Selling": [
        {"field": "Situation",   "definition": "Current customer environment"},
        {"field": "Problem",     "definition": "Existing issue/friction"},
        {"field": "Implication", "definition": "Business consequences of problem"},
        {"field": "Need-Payoff", "definition": "Value of solving the issue"},
    ],
    "MEDDPICC": [
        {"field": "Metrics",          "definition": "Quantified business impact"},
        {"field": "Economic Buyer",   "definition": "Final financial approver"},
        {"field": "Decision Criteria","definition": "Vendor evaluation standards"},
        {"field": "Decision Process", "definition": "Internal approval workflow"},
        {"field": "Paper Process",    "definition": "Procurement/legal contract steps"},
        {"field": "Identify Pain",    "definition": "Critical business challenge"},
        {"field": "Champion",         "definition": "Internal supporter influencing deal"},
        {"field": "Competition",      "definition": "Alternative vendors or status quo"},
    ],
}


async def _seed_defaults():
    """Insert the 6 default methodologies if they don't already exist in DB."""
    col = get_sales_methodology_collection()
    for name, fields in DEFAULT_METHODOLOGIES.items():
        key = name.upper().replace(" ", "_")
        existing = await col.find_one({"_id": key})
        if not existing:
            now = current_timestamp()
            await col.insert_one({
                "_id":         key,
                "name":        name,
                "is_default":  True,
                "core_fields": fields,
                "company_id":  None,
                "meeting_id":  None,
                "created_at":  now,
                "updated_at":  now,
            })


def _doc_to_response(doc: dict) -> dict:
    """Normalize a MongoDB document for API response."""
    doc["id"] = str(doc.pop("_id"))
    return doc


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=dict)
async def list_methodologies(company_id: Optional[str] = None, meeting_id: Optional[str] = None):
    """
    List all sales methodologies with their core fields and quick definitions.
    Supports optional query parameters `company_id` and `meeting_id` to filter results.
    Default methodologies are seeded automatically on first call.
    """
    await _seed_defaults()
    col = get_sales_methodology_collection()

    query = {}
    if company_id or meeting_id:
        conditions = [{"is_default": True}]
        if company_id:
            conditions.append({"company_id": company_id})
        if meeting_id:
            conditions.append({"meeting_id": meeting_id})
        query = {"$or": conditions}

    methodologies = []
    async for doc in col.find(query):
        methodologies.append(_doc_to_response(doc))

    return build_api_response(
        success=True,
        data={
            "methodologies": methodologies,
            "total": len(methodologies),
        },
        message=f"{len(methodologies)} methodologies found"
    )


@router.get("/{name}", response_model=dict)
async def get_methodology(name: str):
    """
    Get a specific methodology by name (case-insensitive search).
    Returns its core fields and quick definitions.

    Example: GET /api/methodology/MEDDIC
             GET /api/methodology/bant
             GET /api/methodology/Value Selling
    """
    await _seed_defaults()
    col = get_sales_methodology_collection()

    # Normalize: try exact _id match first (stored as UPPER_SNAKE)
    key = name.strip().upper().replace(" ", "_")
    doc = await col.find_one({"_id": key})

    # Fallback: case-insensitive name match
    if not doc:
        async for d in col.find():
            if d.get("name", "").lower() == name.strip().lower():
                doc = d
                break

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Methodology '{name}' not found. "
                   f"Use GET /api/methodology/ to see all available methodologies."
        )

    return build_api_response(
        success=True,
        data=_doc_to_response(doc),
    )


@router.post("/", response_model=dict)
async def create_or_update_methodology(body: SalesMethodologyCreate):
    """
    Create a new sales methodology (or update an existing one) with:
      - name          : methodology name (e.g. "My Custom Framework")
      - core_fields   : list of { field, definition } pairs
      - company_id    : optional company ID
      - meeting_id    : optional meeting ID

    If a methodology with the same name already exists, its core fields
    will be updated (upsert behaviour).

    Body example:
    {
      "name": "Value Selling",
      "core_fields": [
        { "field": "Business Value", "definition": "Measurable customer gain" },
        { "field": "ROI",            "definition": "Financial return expected" }
      ],
      "company_id": "abc123",
      "meeting_id": "meet456"
    }
    """
    col = get_sales_methodology_collection()
    key = body.name.strip().upper().replace(" ", "_")

    if not key:
        raise HTTPException(status_code=400, detail="Methodology name cannot be empty")
    if not body.core_fields:
        raise HTTPException(status_code=400, detail="At least one core field is required")

    now = current_timestamp()
    existing = await col.find_one({"_id": key})

    fields_list = [cf.dict() for cf in body.core_fields]

    if existing:
        # Update core fields + updated_at; keep is_default flag unchanged
        await col.update_one(
            {"_id": key},
            {"$set": {
                "name":        body.name.strip(),
                "core_fields": fields_list,
                "company_id":  body.company_id,
                "meeting_id":  body.meeting_id,
                "updated_at":  now,
            }}
        )
        action = "updated"
    else:
        await col.insert_one({
            "_id":         key,
            "name":        body.name.strip(),
            "is_default":  False,
            "core_fields": fields_list,
            "company_id":  body.company_id,
            "meeting_id":  body.meeting_id,
            "created_at":  now,
            "updated_at":  now,
        })
        action = "created"

    updated_doc = await col.find_one({"_id": key})
    return build_api_response(
        success=True,
        data=_doc_to_response(updated_doc),
        message=f"Methodology '{body.name}' {action} successfully"
    )


@router.delete("/{name}", response_model=dict)
async def delete_methodology(name: str):
    """
    Delete a custom methodology.
    Default methodologies (Value Selling, MEDDIC, BANT, SPIN Selling,
    Challenger Sales, MEDDPICC) cannot be deleted.
    """
    col = get_sales_methodology_collection()
    key = name.strip().upper().replace(" ", "_")

    doc = await col.find_one({"_id": key})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Methodology '{name}' not found")

    if doc.get("is_default"):
        raise HTTPException(
            status_code=400,
            detail=f"'{doc['name']}' is a default methodology and cannot be deleted. "
                   "You may update its core fields using POST."
        )

    await col.delete_one({"_id": key})
    return build_api_response(
        success=True,
        message=f"Methodology '{doc['name']}' deleted successfully"
    )
