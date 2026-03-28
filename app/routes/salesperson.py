from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import List, Optional, Annotated
from pydantic import BaseModel
from app.models.schemas import SalespersonCreate, SalespersonResponse, ProductMaterial
from app.config.database import (
    get_salesperson_collection, get_meeting_collection,
    get_conversation_collection
)
from app.services.openai_service import openai_service
from app.services.s3_service import s3_service
from app.utils.helpers import (
    generate_id, current_timestamp, validate_file_type,
    get_content_type, build_api_response
)

router = APIRouter(prefix="/api/salesperson", tags=["Salesperson"])


@router.post(
    "/with-files",
    response_model=dict,
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["product_name"],
                        "properties": {
                            "product_name": {"type": "string"},
                            "description": {"type": "string"},
                            "product_url": {"type": "string", "nullable": True},
                            "materials": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "format": "binary"
                                }
                            }
                        }
                    }
                }
            },
            "required": True
        }
    }
)
async def create_salesperson_with_files(request: Request):
    form = await request.form()

    product_name = form.get("product_name")
    description = form.get("description")
    product_url = form.get("product_url")
    materials = form.getlist("materials")

    try:
        uploaded_materials = []

        if materials:
            allowed_types = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']

            for material in materials:
                if not hasattr(material, 'filename') or not material.filename:
                    continue

                if not validate_file_type(material.filename, allowed_types):
                    raise HTTPException(
                        status_code=400,
                        detail=f"File type not allowed: {material.filename}. Allowed: {', '.join(allowed_types)}"
                    )

                file_bytes = await material.read()
                content_type = get_content_type(material.filename)
                s3_url = await s3_service.upload_document(
                    file_bytes=file_bytes,
                    filename=material.filename,
                    content_type=content_type,
                    folder="sales_materials"
                )

                uploaded_materials.append({
                    "file_name": material.filename,
                    "file_url": s3_url,
                    "file_type": material.filename.split('.')[-1].lower()
                })

        if not product_name:
            raise HTTPException(status_code=400, detail="product_name is required")

        salesperson_id = generate_id()

        salesperson_doc = {
            "_id": salesperson_id,
            "product_name": product_name,
            "product_url": product_url,
            "description": description,
            "materials": uploaded_materials,
            "created_at": current_timestamp(),
            "updated_at": current_timestamp()
        }

        collection = get_salesperson_collection()
        await collection.insert_one(salesperson_doc)

        return build_api_response(
            success=True,
            data={
                "salesperson_id": salesperson_id,
                "product_name": product_name,
                "materials_uploaded": len(uploaded_materials)
            },
            message="Salesperson profile created successfully with materials"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating salesperson: {str(e)}")


@router.get("/health", response_model=dict)
async def salesperson_health():
    """Health check for salesperson endpoints"""
    return build_api_response(
        success=True,
        data={"status": "healthy", "service": "salesperson"},
        message="Salesperson service is running"
    )


@router.get("/{salesperson_id}", response_model=dict)
async def get_salesperson_data(salesperson_id: str):
    """Get salesperson data by ID"""
    try:
        collection = get_salesperson_collection()
        salesperson = await collection.find_one({"_id": salesperson_id})

        if not salesperson:
            raise HTTPException(status_code=404, detail="Salesperson not found")

        salesperson["id"] = str(salesperson.pop("_id"))

        return build_api_response(success=True, data=salesperson)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{salesperson_id}", response_model=dict)
async def update_salesperson_data(
    salesperson_id: str,
    product_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    product_url: Optional[str] = Form(None),
    materials: Annotated[Optional[List[UploadFile]], File(description="PDF, PPTX, DOC, Images")] = None
):
    """Update salesperson data"""
    try:
        collection = get_salesperson_collection()

        existing = await collection.find_one({"_id": salesperson_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Salesperson not found")

        update_data = {"updated_at": current_timestamp()}

        if product_name:
            update_data["product_name"] = product_name
        if description:
            update_data["description"] = description
        if product_url:
            update_data["product_url"] = product_url

        if materials:
            uploaded_materials = []
            allowed_types = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']

            for material in materials:
                if not material.filename:
                    continue

                if not validate_file_type(material.filename, allowed_types):
                    raise HTTPException(
                        status_code=400,
                        detail=f"File type not allowed: {material.filename}"
                    )

                file_bytes = await material.read()
                content_type = get_content_type(material.filename)
                s3_url = await s3_service.upload_document(
                    file_bytes=file_bytes,
                    filename=material.filename,
                    content_type=content_type,
                    folder="sales_materials"
                )

                uploaded_materials.append({
                    "file_name": material.filename,
                    "file_url": s3_url,
                    "file_type": material.filename.split('.')[-1].lower()
                })

            current_materials = existing.get("materials", [])
            update_data["materials"] = current_materials + uploaded_materials

        await collection.update_one(
            {"_id": salesperson_id},
            {"$set": update_data}
        )

        return build_api_response(
            success=True,
            data={"salesperson_id": salesperson_id},
            message="Salesperson profile updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{salesperson_id}", response_model=dict)
async def delete_salesperson_data(salesperson_id: str):
    """Delete salesperson data"""
    try:
        collection = get_salesperson_collection()
        result = await collection.delete_one({"_id": salesperson_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Salesperson not found")

        return build_api_response(
            success=True,
            message="Salesperson profile deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-insights", response_model=dict)
async def get_latest_salesperson_ai_insights():
    """
    Get dynamic aggregate AI insights for the latest salesperson.
    Useful when the client doesn't have the salesperson_id handy.
    """
    try:
        salesperson_col = get_salesperson_collection()
        # Find the most recently updated salesperson
        salesperson = await salesperson_col.find_one({}, sort=[("updated_at", -1)])
        
        if not salesperson:
            raise HTTPException(status_code=404, detail="No salesperson profiles found")
            
        salesperson_id = str(salesperson["_id"])
        # Reuse the existing logic
        return await get_salesperson_ai_insights(salesperson_id)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_latest_salesperson_ai_insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{salesperson_id}/ai-insights", response_model=dict)
async def get_salesperson_ai_insights(salesperson_id: str):
    """
    Get dynamic aggregate AI insights for a salesperson.
    Analyzes performance across all completed meetings.
    """
    try:
        salesperson_col = get_salesperson_collection()
        salesperson = await salesperson_col.find_one({"_id": salesperson_id})
        if not salesperson:
            raise HTTPException(status_code=404, detail="Salesperson not found")

        meeting_col = get_meeting_collection()
        conversation_col = get_conversation_collection()

        meetings_summary = []
        async for meeting in meeting_col.find({"salesperson_id": salesperson_id}):
            meeting_id = str(meeting["_id"])
            
            # Get the latest conversation/analytics for this meeting
            conv = await conversation_col.find_one(
                {"meeting_id": meeting_id},
                sort=[("attempt_number", -1)]
            )
            
            if conv and "analytics" in conv:
                analytics = conv["analytics"]
                meetings_summary.append({
                    "meeting_id": meeting_id,
                    "meeting_goal": meeting.get("meeting_goal"),
                    "score": analytics.get("overall_score", 0),
                    "questions_asked": analytics.get("questions_asked", 0),
                    "open_questions": analytics.get("open_questions", 0),
                    "engagement_score": analytics.get("engagement_score", 0)
                })

        if not meetings_summary:
            return build_api_response(
                success=True,
                data={
                    "strength": "Not enough data yet.",
                    "improvement": "Complete your first few practice sessions to see insights.",
                    "pattern": "Analyzing your performance trends."
                },
                message="No meeting data found for insights."
            )

        # Generate aggregate insights via OpenAI
        insights = await openai_service.generate_salesperson_insights(
            salesperson_data=salesperson,
            meetings_summary=meetings_summary
        )

        return build_api_response(
            success=True,
            data=insights,
            message="Salesperson insights generated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_salesperson_ai_insights: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
