

# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from typing import List, Optional
# from app.models.schemas import SalespersonCreate, SalespersonResponse, ProductMaterial
# from app.config.database import get_salesperson_collection
# from app.services.s3_service import s3_service
# from app.utils.helpers import (
#     generate_id, current_timestamp, validate_file_type,
#     get_content_type, build_api_response
# )

# router = APIRouter(prefix="/api/salesperson", tags=["Salesperson"])


# @router.post("/create-simple", response_model=dict)
# async def create_salesperson_simple(
#     product_name: str = Form(...),
#     description: str = Form(...),
#     product_url: Optional[str] = Form(None)
# ):
#     """
#     Create salesperson profile (Simple - No file uploads)
#     Use this endpoint for quick testing without files
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
#                 "product_name": product_name
#             },
#             message="Salesperson data created successfully"
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/create", response_model=dict)
# async def create_salesperson_data(
#     product_name: str = Form(...),
#     description: str = Form(...),
#     product_url: Optional[str] = Form(None),
#     materials: Optional[List[UploadFile]] = File(default=None)
# ):
#     """
#     Create salesperson profile with product/service details
#     Upload product materials (PDF, PPTX, DOC, Images) - OPTIONAL
    
#     Note: Leave 'materials' empty if you don't want to upload files
#     """
    
#     try:
#         # Upload materials to S3
#         uploaded_materials = []
        
#         if materials and materials[0].filename:
#             allowed_types = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']
            
#             for material in materials:
#                 # Validate file type
#                 if not validate_file_type(material.filename, allowed_types):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"File type not allowed: {material.filename}"
#                     )
                
#                 # Read file
#                 file_bytes = await material.read()
                
#                 # Upload to S3
#                 content_type = get_content_type(material.filename)
#                 s3_url = await s3_service.upload_document(
#                     file_bytes=file_bytes,
#                     filename=material.filename,
#                     content_type=content_type,
#                     folder="sales_materials"
#                 )
                
#                 uploaded_materials.append({
#                     "file_name": material.filename,
#                     "file_url": s3_url,
#                     "file_type": material.filename.split('.')[-1].lower()
#                 })
        
#         # Create salesperson document
#         salesperson_id = generate_id()
        
#         salesperson_doc = {
#             "_id": salesperson_id,
#             "product_name": product_name,
#             "product_url": product_url,
#             "description": description,
#             "materials": uploaded_materials,
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
#                 "materials_uploaded": len(uploaded_materials)
#             },
#             message="Salesperson data created successfully"
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{salesperson_id}", response_model=dict)
# async def get_salesperson_data(salesperson_id: str):
#     """Get salesperson data by ID"""
    
#     try:
#         collection = get_salesperson_collection()
#         salesperson = await collection.find_one({"_id": salesperson_id})
        
#         if not salesperson:
#             raise HTTPException(status_code=404, detail="Salesperson not found")
        
#         # Convert ObjectId to string
#         salesperson["id"] = str(salesperson.pop("_id"))
        
#         return build_api_response(
#             success=True,
#             data=salesperson
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.put("/{salesperson_id}", response_model=dict)
# async def update_salesperson_data(
#     salesperson_id: str,
#     product_name: Optional[str] = Form(None),
#     description: Optional[str] = Form(None),
#     product_url: Optional[str] = Form(None),
#     materials: Optional[List[UploadFile]] = File(None)
# ):
#     """Update salesperson data"""
    
#     try:
#         collection = get_salesperson_collection()
        
#         # Check if exists
#         existing = await collection.find_one({"_id": salesperson_id})
#         if not existing:
#             raise HTTPException(status_code=404, detail="Salesperson not found")
        
#         # Prepare update data
#         update_data = {"updated_at": current_timestamp()}
        
#         if product_name:
#             update_data["product_name"] = product_name
#         if description:
#             update_data["description"] = description
#         if product_url:
#             update_data["product_url"] = product_url
        
#         # Upload new materials if provided
#         if materials:
#             uploaded_materials = []
#             allowed_types = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']
            
#             for material in materials:
#                 if not validate_file_type(material.filename, allowed_types):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"File type not allowed: {material.filename}"
#                     )
                
#                 file_bytes = await material.read()
#                 content_type = get_content_type(material.filename)
#                 s3_url = await s3_service.upload_document(
#                     file_bytes=file_bytes,
#                     filename=material.filename,
#                     content_type=content_type,
#                     folder="sales_materials"
#                 )
                
#                 uploaded_materials.append({
#                     "file_name": material.filename,
#                     "file_url": s3_url,
#                     "file_type": material.filename.split('.')[-1].lower()
#                 })
            
#             # Append to existing materials
#             update_data["$push"] = {"materials": {"$each": uploaded_materials}}
        
#         # Update in MongoDB
#         await collection.update_one(
#             {"_id": salesperson_id},
#             {"$set": update_data}
#         )
        
#         return build_api_response(
#             success=True,
#             message="Salesperson data updated successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/{salesperson_id}", response_model=dict)
# async def delete_salesperson_data(salesperson_id: str):
#     """Delete salesperson data"""
    
#     try:
#         collection = get_salesperson_collection()
        
#         result = await collection.delete_one({"_id": salesperson_id})
        
#         if result.deleted_count == 0:
#             raise HTTPException(status_code=404, detail="Salesperson not found")
        
#         return build_api_response(
#             success=True,
#             message="Salesperson data deleted successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))









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


@router.post("/simple", response_model=dict)
async def create_salesperson_simple_json(request: SalespersonSimpleRequest):
    """
    Create salesperson profile (Simple - No file uploads)
    Accepts JSON data - for frontend API calls
    
    Endpoint: POST /api/salesperson/simple
    Body: {
        "product_name": "Product Name",
        "description": "Product description",
        "product_url": "https://example.com" (optional)
    }
    """
    
    try:
        # Create salesperson document
        salesperson_id = generate_id()
        
        salesperson_doc = {
            "_id": salesperson_id,
            "product_name": request.product_name,
            "product_url": request.product_url,
            "description": request.description,
            "materials": [],
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
                "product_name": request.product_name,
                "materials_uploaded": 0
            },
            message="Salesperson profile created successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-simple", response_model=dict)
async def create_salesperson_simple_form(
    product_name: str = Form(...),
    description: str = Form(...),
    product_url: Optional[str] = Form(None)
):
    """
    Create salesperson profile (Simple - No file uploads)
    Accepts Form data - for Swagger/direct form submission
    
    Endpoint: POST /api/salesperson/create-simple
    """
    
    try:
        # Create salesperson document
        salesperson_id = generate_id()
        
        salesperson_doc = {
            "_id": salesperson_id,
            "product_name": product_name,
            "product_url": product_url,
            "description": description,
            "materials": [],
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
                "materials_uploaded": 0
            },
            message="Salesperson profile created successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/with-files", response_model=dict)
async def create_salesperson_with_files(
    product_name: str = Form(...),
    description: str = Form(...),
    product_url: Optional[str] = Form(None),
    materials: Optional[List[UploadFile]] = File(default=None)
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


@router.post("/create", response_model=dict)
async def create_salesperson_legacy(
    product_name: str = Form(...),
    description: str = Form(...),
    product_url: Optional[str] = Form(None),
    materials: Optional[List[UploadFile]] = File(default=None)
):
    """
    Legacy endpoint - redirects to /with-files
    Kept for backward compatibility
    """
    return await create_salesperson_with_files(
        product_name=product_name,
        description=description,
        product_url=product_url,
        materials=materials
    )


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