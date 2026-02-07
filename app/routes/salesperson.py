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


# @router.post("/create", response_model=dict)
# async def create_salesperson_data(
#     product_name: str = Form(..., description="Name of the product or service"),
#     description: str = Form(..., description="Detailed description"),
#     product_url: Optional[str] = Form(None, description="Optional product URL"),
#     materials: List[UploadFile] = File(default=[], description="Product materials (PDF, PPTX, DOC, Images)")
# ):
#     """
#     Create salesperson profile with product/service details
#     Upload product materials (PDF, PPTX, DOC, Images)
    
#     Args:
#         product_name: Name of the product/service
#         description: Detailed description
#         product_url: Optional URL to product page
#         materials: List of files to upload
#     """
    
#     try:
#         # Upload materials to S3
#         uploaded_materials = []
        
#         if materials:
#             allowed_types = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']
            
#             for material in materials:
#                 # Skip if no filename (empty file input)
#                 if not material.filename:
#                     continue
                    
#                 # Validate file type
#                 if not validate_file_type(material.filename, allowed_types):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"File type not allowed: {material.filename}. Allowed types: {', '.join(allowed_types)}"
#                     )
                
#                 # Read file
#                 file_bytes = await material.read()
                
#                 # Check file size (optional - e.g., max 10MB)
#                 if len(file_bytes) > 10 * 1024 * 1024:  # 10MB
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"File too large: {material.filename}. Maximum size is 10MB"
#                     )
                
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
#                     "file_type": material.filename.split('.')[-1].lower(),
#                     "file_size": len(file_bytes)
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
#                 "product_name": product_name,
#                 "materials_uploaded": len(uploaded_materials)
#             },
#             message="Salesperson data created successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to create salesperson data: {str(e)}")


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
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve salesperson data: {str(e)}")


# @router.get("/", response_model=dict)
# async def list_all_salespersons(skip: int = 0, limit: int = 10):
#     """List all salesperson data with pagination"""
    
#     try:
#         collection = get_salesperson_collection()
        
#         # Get total count
#         total = await collection.count_documents({})
        
#         # Get paginated results
#         cursor = collection.find({}).skip(skip).limit(limit).sort("created_at", -1)
#         salespersons = await cursor.to_list(length=limit)
        
#         # Convert ObjectId to string
#         for sp in salespersons:
#             sp["id"] = str(sp.pop("_id"))
        
#         return build_api_response(
#             success=True,
#             data={
#                 "salespersons": salespersons,
#                 "total": total,
#                 "skip": skip,
#                 "limit": limit
#             }
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to list salespersons: {str(e)}")


# @router.put("/{salesperson_id}", response_model=dict)
# async def update_salesperson_data(
#     salesperson_id: str,
#     product_name: Optional[str] = Form(None),
#     description: Optional[str] = Form(None),
#     product_url: Optional[str] = Form(None),
#     materials: List[UploadFile] = File(default=[])
# ):
#     """
#     Update salesperson data
#     New materials will be appended to existing ones
#     """
    
#     try:
#         collection = get_salesperson_collection()
        
#         # Check if exists
#         existing = await collection.find_one({"_id": salesperson_id})
#         if not existing:
#             raise HTTPException(status_code=404, detail="Salesperson not found")
        
#         # Prepare update data
#         update_data = {"updated_at": current_timestamp()}
        
#         if product_name is not None:
#             update_data["product_name"] = product_name
#         if description is not None:
#             update_data["description"] = description
#         if product_url is not None:
#             update_data["product_url"] = product_url
        
#         # Upload new materials if provided
#         uploaded_materials = []
#         if materials:
#             allowed_types = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']
            
#             for material in materials:
#                 # Skip if no filename
#                 if not material.filename:
#                     continue
                    
#                 if not validate_file_type(material.filename, allowed_types):
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"File type not allowed: {material.filename}"
#                     )
                
#                 file_bytes = await material.read()
                
#                 # Check file size
#                 if len(file_bytes) > 10 * 1024 * 1024:
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"File too large: {material.filename}. Maximum size is 10MB"
#                     )
                
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
#                     "file_type": material.filename.split('.')[-1].lower(),
#                     "file_size": len(file_bytes)
#                 })
        
#         # Update in MongoDB
#         if uploaded_materials:
#             # Append new materials to existing ones
#             await collection.update_one(
#                 {"_id": salesperson_id},
#                 {
#                     "$set": update_data,
#                     "$push": {"materials": {"$each": uploaded_materials}}
#                 }
#             )
#         else:
#             # Just update basic fields
#             await collection.update_one(
#                 {"_id": salesperson_id},
#                 {"$set": update_data}
#             )
        
#         return build_api_response(
#             success=True,
#             data={
#                 "salesperson_id": salesperson_id,
#                 "new_materials_uploaded": len(uploaded_materials)
#             },
#             message="Salesperson data updated successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to update salesperson data: {str(e)}")


# @router.delete("/{salesperson_id}/material/{material_index}", response_model=dict)
# async def delete_material(salesperson_id: str, material_index: int):
#     """Delete a specific material from salesperson"""
    
#     try:
#         collection = get_salesperson_collection()
        
#         # Get salesperson
#         salesperson = await collection.find_one({"_id": salesperson_id})
#         if not salesperson:
#             raise HTTPException(status_code=404, detail="Salesperson not found")
        
#         # Check if material index is valid
#         if material_index < 0 or material_index >= len(salesperson.get("materials", [])):
#             raise HTTPException(status_code=400, detail="Invalid material index")
        
#         # Remove material at index
#         materials = salesperson.get("materials", [])
#         removed_material = materials.pop(material_index)
        
#         # Update document
#         await collection.update_one(
#             {"_id": salesperson_id},
#             {
#                 "$set": {
#                     "materials": materials,
#                     "updated_at": current_timestamp()
#                 }
#             }
#         )
        
#         # Optional: Delete from S3
#         # await s3_service.delete_document(removed_material["file_url"])
        
#         return build_api_response(
#             success=True,
#             data={"removed_material": removed_material["file_name"]},
#             message="Material deleted successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to delete material: {str(e)}")


# @router.delete("/{salesperson_id}", response_model=dict)
# async def delete_salesperson_data(salesperson_id: str):
#     """Delete salesperson data"""
    
#     try:
#         collection = get_salesperson_collection()
        
#         # Get salesperson to retrieve materials for cleanup
#         salesperson = await collection.find_one({"_id": salesperson_id})
        
#         if not salesperson:
#             raise HTTPException(status_code=404, detail="Salesperson not found")
        
#         # Delete from MongoDB
#         result = await collection.delete_one({"_id": salesperson_id})
        
#         if result.deleted_count == 0:
#             raise HTTPException(status_code=404, detail="Salesperson not found")
        
#         # Optional: Delete materials from S3
#         # for material in salesperson.get("materials", []):
#         #     await s3_service.delete_document(material["file_url"])
        
#         return build_api_response(
#             success=True,
#             message="Salesperson data deleted successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to delete salesperson data: {str(e)}")




from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from app.models.schemas import SalespersonCreate, SalespersonResponse, ProductMaterial
from app.config.database import get_salesperson_collection
from app.services.s3_service import s3_service
from app.utils.helpers import (
    generate_id, current_timestamp, validate_file_type,
    get_content_type, build_api_response
)

router = APIRouter(prefix="/api/salesperson", tags=["Salesperson"])


@router.post("/create-simple", response_model=dict)
async def create_salesperson_simple(
    product_name: str = Form(...),
    description: str = Form(...),
    product_url: Optional[str] = Form(None)
):
    """
    Create salesperson profile (Simple - No file uploads)
    Use this endpoint for quick testing without files
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
                "product_name": product_name
            },
            message="Salesperson data created successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=dict)
async def create_salesperson_data(
    product_name: str = Form(...),
    description: str = Form(...),
    product_url: Optional[str] = Form(None),
    materials: Optional[List[UploadFile]] = File(default=None)
):
    """
    Create salesperson profile with product/service details
    Upload product materials (PDF, PPTX, DOC, Images) - OPTIONAL
    
    Note: Leave 'materials' empty if you don't want to upload files
    """
    
    try:
        # Upload materials to S3
        uploaded_materials = []
        
        if materials and materials[0].filename:
            allowed_types = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']
            
            for material in materials:
                # Validate file type
                if not validate_file_type(material.filename, allowed_types):
                    raise HTTPException(
                        status_code=400,
                        detail=f"File type not allowed: {material.filename}"
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
                "materials_uploaded": len(uploaded_materials)
            },
            message="Salesperson data created successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{salesperson_id}", response_model=dict)
async def get_salesperson_data(salesperson_id: str):
    """Get salesperson data by ID"""
    
    try:
        collection = get_salesperson_collection()
        salesperson = await collection.find_one({"_id": salesperson_id})
        
        if not salesperson:
            raise HTTPException(status_code=404, detail="Salesperson not found")
        
        # Convert ObjectId to string
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
    """Update salesperson data"""
    
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
        if materials:
            uploaded_materials = []
            allowed_types = ['pdf', 'pptx', 'ppt', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']
            
            for material in materials:
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
            
            # Append to existing materials
            update_data["$push"] = {"materials": {"$each": uploaded_materials}}
        
        # Update in MongoDB
        await collection.update_one(
            {"_id": salesperson_id},
            {"$set": update_data}
        )
        
        return build_api_response(
            success=True,
            message="Salesperson data updated successfully"
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
            message="Salesperson data deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))