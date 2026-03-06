from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel
from app.models.schemas import SalespersonCreate, SalespersonResponse, ProductMaterial
from app.config.database import get_salesperson_collection
from app.services.s3_service import s3_service
from app.utils.helpers import (
    generate_id, current_timestamp, validate_file_type,
    get_content_type, build_api_response
)

router = APIRouter(prefix="/api/salesperson", tags=["Salesperson"])


# Pydantic model for JSON requests
class SalespersonSimpleRequest(BaseModel):
    product_name: str
    description: str
    product_url: Optional[str] = None


# @router.post("/simple", response_model=dict)
# async def create_salesperson_simple_json(request: SalespersonSimpleRequest):
#     """
#     Create salesperson profile (Simple - No file uploads)
#     Accepts JSON data - for frontend API calls
    
#     Endpoint: POST /api/salesperson/simple
#     Body: {
#         "product_name": "Product Name",
#         "description": "Product description",
#         "product_url": "https://example.com" (optional)
#     }
#     """
    
#     try:
#         # Create salesperson document
#         salesperson_id = generate_id()
        
#         salesperson_doc = {
#             "_id": salesperson_id,
#             "product_name": request.product_name,
#             "product_url": request.product_url,
#             "description": request.description,
#             "materials": [],
#             "created_at": current_timestamp(),
#             "updated_at": current_timestamp()
#         }
        
#         # Insert into MongoDB
#         collection = get_salesperson_collection()
#         await collection.insert_one(salesperson_doc)
        
#         return build_api_response(
#             success=True,
#             data={
#                 "salesperson_id": salesperson_id,
#                 "product_name": request.product_name,
#                 "materials_uploaded": 0
#             },
#             message="Salesperson profile created successfully"
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/create-simple", response_model=dict)
# async def create_salesperson_simple_form(
#     product_name: str = Form(...),
#     description: str = Form(...),
#     product_url: Optional[str] = Form(None)
# ):
#     """
#     Create salesperson profile (Simple - No file uploads)
#     Accepts Form data - for Swagger/direct form submission
    
#     Endpoint: POST /api/salesperson/create-simple
#     """
    
#     try:
#         # Create salesperson document
#         salesperson_id = generate_id()
        
#         salesperson_doc = {
#             "_id": salesperson_id,
#             "product_name": product_name,
#             "product_url": product_url,
#             "description": description,
#             "materials": [],
#             "created_at": current_timestamp(),
#             "updated_at": current_timestamp()
#         }
        
#         # Insert into MongoDB
#         collection = get_salesperson_collection()
#         await collection.insert_one(salesperson_doc)
        
#         return build_api_response(
#             success=True,
#             data={
#                 "salesperson_id": salesperson_id,
#                 "product_name": product_name,
#                 "materials_uploaded": 0
#             },
#             message="Salesperson profile created successfully"
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.post("/with-files", response_model=dict)
async def create_salesperson_with_files(
    product_name: str = Form(...),
    description: str = Form(...),
    product_url: Optional[str] = Form(None),
    # materials: Optional[List[UploadFile]] = File(default=None),
    materials: List[UploadFile]= File(default=None)
):
    """
    Create salesperson profile with file uploads
    
    Endpoint: POST /api/salesperson/with-files
    Content-Type: multipart/form-data
    
    Form Fields:
    - product_name: string (required)
    - description: string (required)
    - product_url: string (optional)
    - materials: files[] (optional) - PDF, PPTX, DOC, Images
    """
    
    try:
        # Upload materials to S3
        uploaded_materials = []
        
        if materials and len(materials) > 0:
            allowed_types = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']
            
            for material in materials:
                # Skip if no filename (empty upload)
                if not material.filename:
                    continue
                
                # Validate file type
                if not validate_file_type(material.filename, allowed_types):
                    raise HTTPException(
                        status_code=400,
                        detail=f"File type not allowed: {material.filename}. Allowed: {', '.join(allowed_types)}"
                    )
                
                # Read file
                file_bytes = await material.read()
                
                # Upload to S3
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
        
        # Create salesperson document
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
        
        # Insert into MongoDB
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


# @router.post("/create", response_model=dict)
# async def create_salesperson_legacy(
#     product_name: str = Form(...),
#     description: str = Form(...),
#     product_url: Optional[str] = Form(None),
#     materials: Optional[List[UploadFile]] = File(default=None)
# ):
#     """
#     Legacy endpoint - redirects to /with-files
#     Kept for backward compatibility
#     """
#     return await create_salesperson_with_files(
#         product_name=product_name,
#         description=description,
#         product_url=product_url,
#         materials=materials
#     )


@router.get("/{salesperson_id}", response_model=dict)
async def get_salesperson_data(salesperson_id: str):
    """
    Get salesperson data by ID
    
    Endpoint: GET /api/salesperson/{salesperson_id}
    """
    
    try:
        collection = get_salesperson_collection()
        salesperson = await collection.find_one({"_id": salesperson_id})
        
        if not salesperson:
            raise HTTPException(status_code=404, detail="Salesperson not found")
        
        # Convert _id to id for consistency
        salesperson["id"] = str(salesperson.pop("_id"))
        
        return build_api_response(
            success=True,
            data=salesperson
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{salesperson_id}/analytics", response_model=dict)
async def get_salesperson_analytics(salesperson_id: str):
    """
    Get aggregated analytics for a salesperson across all their meetings/sessions.
    Endpoint: GET /api/salesperson/{salesperson_id}/analytics
    """
    try:
        from app.config.database import get_meeting_collection, get_conversation_collection
        
        # 1. Find all meetings for this salesperson
        meeting_col = get_meeting_collection()
        meetings = await meeting_col.find({"salesperson_id": salesperson_id}).to_list(length=None)
        
        if not meetings:
            return build_api_response(success=True, data={
                "total_sessions": 0, "message": "No meetings found for this salesperson."
            })
            
        meeting_ids = [m["_id"] for m in meetings]
        
        # 2. Find all conversation sessions for these meetings
        conv_col = get_conversation_collection()
        cursor = conv_col.find({"meeting_id": {"$in": meeting_ids}})
        
        total_sessions = 0
        total_score = 0
        scored_sessions = 0
        total_sp_time = 0
        total_ai_time = 0
        sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        all_risks = []
        all_opportunities = []
        
        async for session in cursor:
            total_sessions += 1
            total_sp_time += session.get("salesperson_talk_time", 0)
            total_ai_time += session.get("representatives_talk_time", 0)
            
            # Aggregate AI analytics if present
            analytics = session.get("analytics")
            if analytics:
                score = analytics.get("overall_score", 0)
                if score > 0:
                    total_score += score
                    scored_sessions += 1
                
                sentiment = analytics.get("sentiment")
                if sentiment in sentiment_counts:
                    sentiment_counts[sentiment] += 1
                
                all_risks.extend(analytics.get("risks", []))
                all_opportunities.extend(analytics.get("opportunities", []))
                
        if total_sessions == 0:
            return build_api_response(success=True, data={
                "total_sessions": 0, "message": "No practice sessions recorded yet."
            })
            
        # Calculate final aggregated metrics
        avg_score = round(total_score / scored_sessions, 1) if scored_sessions > 0 else 0
        total_time = total_sp_time + total_ai_time
        sp_ratio = round(total_sp_time / total_time * 100, 1) if total_time > 0 else 0
        ai_ratio = round(total_ai_time / total_time * 100, 1) if total_time > 0 else 0
        
        # Get top 5 risks and opportunities (simple frequency count without heavy NLP logic)
        from collections import Counter
        top_risks = [k for k, v in Counter(all_risks).most_common(5)]
        top_opportunities = [k for k, v in Counter(all_opportunities).most_common(5)]
        
        # Determine dominant sentiment
        dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get) if any(sentiment_counts.values()) else "Neutral"
        
        aggregated_data = {
            "total_sessions": total_sessions,
            "average_engagement_score": avg_score,
            "talk_time_distribution": {
                "salesperson_percentage": sp_ratio,
                "ai_percentage": ai_ratio,
                "total_minutes": round(total_time / 60, 2)
            },
            "dominant_sentiment": dominant_sentiment,
            "sentiment_breakdown": sentiment_counts,
            "top_risks_identified": top_risks,
            "top_opportunities": top_opportunities,
        }
        
        return build_api_response(success=True, data=aggregated_data)
        
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{salesperson_id}", response_model=dict)
async def update_salesperson_data(
    salesperson_id: str,
    product_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    product_url: Optional[str] = Form(None),
    materials: Optional[List[UploadFile]] = File(None)
):
    """
    Update salesperson data
    
    Endpoint: PUT /api/salesperson/{salesperson_id}
    """
    
    try:
        collection = get_salesperson_collection()
        
        # Check if exists
        existing = await collection.find_one({"_id": salesperson_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Salesperson not found")
        
        # Prepare update data
        update_data = {"updated_at": current_timestamp()}
        
        if product_name:
            update_data["product_name"] = product_name
        if description:
            update_data["description"] = description
        if product_url:
            update_data["product_url"] = product_url
        
        # Upload new materials if provided
        if materials and len(materials) > 0:
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
            
            # Get existing materials and append new ones
            current_materials = existing.get("materials", [])
            update_data["materials"] = current_materials + uploaded_materials
        
        # Update in MongoDB
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
    """
    Delete salesperson data
    
    Endpoint: DELETE /api/salesperson/{salesperson_id}
    """
    
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


# Health check endpoint for this router
@router.get("/health", response_model=dict)
async def salesperson_health():
    """Health check for salesperson endpoints"""
    return build_api_response(
        success=True,
        data={"status": "healthy", "service": "salesperson"},
        message="Salesperson service is running"
    )