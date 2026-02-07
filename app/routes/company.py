# from fastapi import APIRouter, HTTPException, Body
# from typing import List
# from app.models.schemas import (
#     CompanyCreate, CompanyResponse, RepresentativeCreate,
#     RepresentativeResponse, MeetingMode
# )
# from app.config.database import get_company_collection, get_representative_collection
# from app.services.scraper import scraper
# from app.utils.helpers import generate_id, current_timestamp, build_api_response

# router = APIRouter(prefix="/api/company", tags=["Company"])


# @router.post("/create", response_model=dict)
# async def create_company_data(company_data: CompanyCreate):
#     """
#     Create company profile by providing URL
#     Automatically scrapes company data from website
#     """
    
#     try:
#         company_id = generate_id()
        
#         # Scrape company data if auto_fetch is enabled
#         scraped_data = {}
#         if company_data.auto_fetch:
#             scraped_data = await scraper.scrape_company_data(str(company_data.company_url))
            
#             # Fetch tech stack
#             tech_stack = await scraper.fetch_tech_stack(str(company_data.company_url))
#             if tech_stack:
#                 scraped_data["tech_stack"] = tech_stack
        
#         # Create company document
#         company_doc = {
#             "_id": company_id,
#             "company_url": str(company_data.company_url),
#             "company_data": scraped_data,
#             "created_at": current_timestamp(),
#             "last_updated": current_timestamp()
#         }
        
#         # Insert into MongoDB
#         collection = get_company_collection()
#         await collection.insert_one(company_doc)
        
#         return build_api_response(
#             success=True,
#             data={
#                 "company_id": company_id,
#                 "company_data": scraped_data
#             },
#             message="Company data created successfully"
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{company_id}", response_model=dict)
# async def get_company_data(company_id: str):
#     """Get company data by ID"""
    
#     try:
#         collection = get_company_collection()
#         company = await collection.find_one({"_id": company_id})
        
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
        
#         company["id"] = str(company.pop("_id"))
        
#         return build_api_response(
#             success=True,
#             data=company
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{company_id}/refresh-data", response_model=dict)
# async def refresh_company_data(company_id: str):
#     """Re-scrape and update company data"""
    
#     try:
#         collection = get_company_collection()
#         company = await collection.find_one({"_id": company_id})
        
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
        
#         # Re-scrape data
#         scraped_data = await scraper.scrape_company_data(company["company_url"])
#         tech_stack = await scraper.fetch_tech_stack(company["company_url"])
        
#         if tech_stack:
#             scraped_data["tech_stack"] = tech_stack
        
#         # Update in database
#         await collection.update_one(
#             {"_id": company_id},
#             {
#                 "$set": {
#                     "company_data": scraped_data,
#                     "last_updated": current_timestamp()
#                 }
#             }
#         )
        
#         return build_api_response(
#             success=True,
#             data={"company_data": scraped_data},
#             message="Company data refreshed successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{company_id}/representatives", response_model=dict)
# async def add_representative(
#     company_id: str,
#     representative: RepresentativeCreate
# ):
#     """Add a company representative for meetings"""
    
#     try:
#         # Verify company exists
#         company_collection = get_company_collection()
#         company = await company_collection.find_one({"_id": company_id})
        
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
        
#         # Create representative
#         rep_id = generate_id()
        
#         rep_doc = {
#             "_id": rep_id,
#             "company_id": company_id,
#             "name": representative.name,
#             "role": representative.role.value,
#             "tenure_months": representative.tenure_months,
#             "personality_traits": [trait.value for trait in representative.personality_traits],
#             "is_decision_maker": representative.is_decision_maker,
#             "linkedin_profile": str(representative.linkedin_profile) if representative.linkedin_profile else None,
#             "notes": representative.notes,
#             "voice_id": representative.voice_id,
#             "created_at": current_timestamp()
#         }
        
#         # Insert into MongoDB
#         rep_collection = get_representative_collection()
#         await rep_collection.insert_one(rep_doc)
        
#         return build_api_response(
#             success=True,
#             data={"representative_id": rep_id},
#             message="Representative added successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{company_id}/representatives", response_model=dict)
# async def get_company_representatives(company_id: str):
#     """Get all representatives for a company"""
    
#     try:
#         rep_collection = get_representative_collection()
        
#         representatives = []
#         async for rep in rep_collection.find({"company_id": company_id}):
#             rep["id"] = str(rep.pop("_id"))
#             rep.pop("company_id", None)
#             representatives.append(rep)
        
#         return build_api_response(
#             success=True,
#             data={"representatives": representatives}
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.put("/representatives/{rep_id}", response_model=dict)
# async def update_representative(
#     rep_id: str,
#     representative: RepresentativeCreate
# ):
#     """Update representative information"""
    
#     try:
#         rep_collection = get_representative_collection()
        
#         # Check if exists
#         existing = await rep_collection.find_one({"_id": rep_id})
#         if not existing:
#             raise HTTPException(status_code=404, detail="Representative not found")
        
#         # Update data
#         update_data = {
#             "name": representative.name,
#             "role": representative.role.value,
#             "tenure_months": representative.tenure_months,
#             "personality_traits": [trait.value for trait in representative.personality_traits],
#             "is_decision_maker": representative.is_decision_maker,
#             "linkedin_profile": str(representative.linkedin_profile) if representative.linkedin_profile else None,
#             "notes": representative.notes,
#             "voice_id": representative.voice_id,
#             "updated_at": current_timestamp()
#         }
        
#         await rep_collection.update_one(
#             {"_id": rep_id},
#             {"$set": update_data}
#         )
        
#         return build_api_response(
#             success=True,
#             message="Representative updated successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/representatives/{rep_id}", response_model=dict)
# async def delete_representative(rep_id: str):
#     """Delete a representative"""
    
#     try:
#         rep_collection = get_representative_collection()
        
#         result = await rep_collection.delete_one({"_id": rep_id})
        
#         if result.deleted_count == 0:
#             raise HTTPException(status_code=404, detail="Representative not found")
        
#         return build_api_response(
#             success=True,
#             message="Representative deleted successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))








# from fastapi import APIRouter, HTTPException, Body
# from typing import List
# from app.models.schemas import (
#     CompanyCreate, CompanyResponse, RepresentativeCreate,
#     RepresentativeResponse, MeetingMode
# )
# from app.config.database import get_company_collection, get_representative_collection
# from app.services.scraper import scraper
# from app.utils.helpers import generate_id, current_timestamp, build_api_response

# router = APIRouter(prefix="/api/company", tags=["Company"])


# @router.post("/create", response_model=dict)
# async def create_company_data(company_data: CompanyCreate):
#     """
#     Create company profile by providing URL
#     Automatically scrapes company data from website
#     """
    
#     try:
#         company_id = generate_id()
        
#         # Scrape company data if auto_fetch is enabled
#         scraped_data = {}
#         if company_data.auto_fetch:
#             scraped_data = await scraper.scrape_company_data(str(company_data.company_url))
        
#         # Create company document
#         company_doc = {
#             "_id": company_id,
#             "company_url": str(company_data.company_url),
#             "company_data": scraped_data,
#             "created_at": current_timestamp(),
#             "last_updated": current_timestamp()
#         }
        
#         # Insert into MongoDB
#         collection = get_company_collection()
#         await collection.insert_one(company_doc)
        
#         return build_api_response(
#             success=True,
#             data={
#                 "company_id": company_id,
#                 "company_data": scraped_data
#             },
#             message="Company data created successfully"
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{company_id}", response_model=dict)
# async def get_company_data(company_id: str):
#     """Get company data by ID"""
    
#     try:
#         collection = get_company_collection()
#         company = await collection.find_one({"_id": company_id})
        
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
        
#         company["id"] = str(company.pop("_id"))
        
#         return build_api_response(
#             success=True,
#             data=company
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{company_id}/refresh-data", response_model=dict)
# async def refresh_company_data(company_id: str):
#     """Re-scrape and update company data"""
    
#     try:
#         collection = get_company_collection()
#         company = await collection.find_one({"_id": company_id})
        
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
        
#         # Re-scrape data
#         scraped_data = await scraper.scrape_company_data(company["company_url"])
        
#         # Update in database
#         await collection.update_one(
#             {"_id": company_id},
#             {
#                 "$set": {
#                     "company_data": scraped_data,
#                     "last_updated": current_timestamp()
#                 }
#             }
#         )
        
#         return build_api_response(
#             success=True,
#             data={"company_data": scraped_data},
#             message="Company data refreshed successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{company_id}/representatives", response_model=dict)
# async def add_representative(
#     company_id: str,
#     representative: RepresentativeCreate
# ):
#     """Add a company representative for meetings"""
    
#     try:
#         # Verify company exists
#         company_collection = get_company_collection()
#         company = await company_collection.find_one({"_id": company_id})
        
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
        
#         # Create representative
#         rep_id = generate_id()
        
#         rep_doc = {
#             "_id": rep_id,
#             "company_id": company_id,
#             "name": representative.name,
#             "role": representative.role.value,
#             "tenure_months": representative.tenure_months,
#             "personality_traits": [trait.value for trait in representative.personality_traits],
#             "is_decision_maker": representative.is_decision_maker,
#             "linkedin_profile": str(representative.linkedin_profile) if representative.linkedin_profile else None,
#             "notes": representative.notes,
#             "voice_id": representative.voice_id,
#             "created_at": current_timestamp()
#         }
        
#         # Insert into MongoDB
#         rep_collection = get_representative_collection()
#         await rep_collection.insert_one(rep_doc)
        
#         return build_api_response(
#             success=True,
#             data={"representative_id": rep_id},
#             message="Representative added successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{company_id}/representatives", response_model=dict)
# async def get_company_representatives(company_id: str):
#     """Get all representatives for a company"""
    
#     try:
#         rep_collection = get_representative_collection()
        
#         representatives = []
#         async for rep in rep_collection.find({"company_id": company_id}):
#             rep["id"] = str(rep.pop("_id"))
#             rep.pop("company_id", None)
#             representatives.append(rep)
        
#         return build_api_response(
#             success=True,
#             data={"representatives": representatives}
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.put("/representatives/{rep_id}", response_model=dict)
# async def update_representative(
#     rep_id: str,
#     representative: RepresentativeCreate
# ):
#     """Update representative information"""
    
#     try:
#         rep_collection = get_representative_collection()
        
#         # Check if exists
#         existing = await rep_collection.find_one({"_id": rep_id})
#         if not existing:
#             raise HTTPException(status_code=404, detail="Representative not found")
        
#         # Update data
#         update_data = {
#             "name": representative.name,
#             "role": representative.role.value,
#             "tenure_months": representative.tenure_months,
#             "personality_traits": [trait.value for trait in representative.personality_traits],
#             "is_decision_maker": representative.is_decision_maker,
#             "linkedin_profile": str(representative.linkedin_profile) if representative.linkedin_profile else None,
#             "notes": representative.notes,
#             "voice_id": representative.voice_id,
#             "updated_at": current_timestamp()
#         }
        
#         await rep_collection.update_one(
#             {"_id": rep_id},
#             {"$set": update_data}
#         )
        
#         return build_api_response(
#             success=True,
#             message="Representative updated successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/representatives/{rep_id}", response_model=dict)
# async def delete_representative(rep_id: str):
#     """Delete a representative"""
    
#     try:
#         rep_collection = get_representative_collection()
        
#         result = await rep_collection.delete_one({"_id": rep_id})
        
#         if result.deleted_count == 0:
#             raise HTTPException(status_code=404, detail="Representative not found")
        
#         return build_api_response(
#             success=True,
#             message="Representative deleted successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))






from fastapi import APIRouter, HTTPException, Body
from typing import List
from app.models.schemas import (
    CompanyCreate, CompanyResponse, RepresentativeCreate,
    RepresentativeResponse, MeetingMode
)
from app.config.database import get_company_collection, get_representative_collection
from app.services.scraper import scraper
from app.utils.helpers import generate_id, current_timestamp, build_api_response

router = APIRouter(prefix="/api/company", tags=["Company"])


@router.post("/create", response_model=dict)
async def create_company_data(company_data: CompanyCreate):
    """Create company profile with AI-powered data extraction"""
    
    try:
        company_id = generate_id()
        
        scraped_data = {}
        if company_data.auto_fetch:
            scraped_data = await scraper.scrape_company_data(str(company_data.company_url))
        
        company_doc = {
            "_id": company_id,
            "company_url": str(company_data.company_url),
            "company_data": scraped_data,
            "created_at": current_timestamp(),
            "last_updated": current_timestamp()
        }
        
        collection = get_company_collection()
        await collection.insert_one(company_doc)
        
        return build_api_response(
            success=True,
            data={
                "company_id": company_id,
                "company_data": scraped_data
            },
            message="Company data created successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}", response_model=dict)
async def get_company_data(company_id: str):
    """Get company data by ID"""
    
    try:
        collection = get_company_collection()
        company = await collection.find_one({"_id": company_id})
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company["id"] = str(company.pop("_id"))
        
        return build_api_response(
            success=True,
            data=company
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{company_id}/representatives", response_model=dict)
async def add_representative(
    company_id: str,
    representative: RepresentativeCreate
):
    """Add a company representative"""
    
    try:
        company_collection = get_company_collection()
        company = await company_collection.find_one({"_id": company_id})
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        rep_id = generate_id()
        
        rep_doc = {
            "_id": rep_id,
            "company_id": company_id,
            "name": representative.name,
            "role": representative.role.value,
            "tenure_months": representative.tenure_months,
            "personality_traits": [trait.value for trait in representative.personality_traits],
            "is_decision_maker": representative.is_decision_maker,
            "linkedin_profile": str(representative.linkedin_profile) if representative.linkedin_profile else None,
            "notes": representative.notes,
            "voice_id": representative.voice_id,
            "created_at": current_timestamp()
        }
        
        rep_collection = get_representative_collection()
        await rep_collection.insert_one(rep_doc)
        
        return build_api_response(
            success=True,
            data={"representative_id": rep_id},
            message="Representative added successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/representatives", response_model=dict)
async def get_company_representatives(company_id: str):
    """Get all representatives for a company"""
    
    try:
        rep_collection = get_representative_collection()
        
        representatives = []
        async for rep in rep_collection.find({"company_id": company_id}):
            rep["id"] = str(rep.pop("_id"))
            rep.pop("company_id", None)
            representatives.append(rep)
        
        return build_api_response(
            success=True,
            data={"representatives": representatives}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/representatives/{rep_id}", response_model=dict)
async def update_representative(
    rep_id: str,
    representative: RepresentativeCreate
):
    """Update representative information"""
    
    try:
        rep_collection = get_representative_collection()
        
        existing = await rep_collection.find_one({"_id": rep_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Representative not found")
        
        update_data = {
            "name": representative.name,
            "role": representative.role.value,
            "tenure_months": representative.tenure_months,
            "personality_traits": [trait.value for trait in representative.personality_traits],
            "is_decision_maker": representative.is_decision_maker,
            "linkedin_profile": str(representative.linkedin_profile) if representative.linkedin_profile else None,
            "notes": representative.notes,
            "voice_id": representative.voice_id,
            "updated_at": current_timestamp()
        }
        
        await rep_collection.update_one(
            {"_id": rep_id},
            {"$set": update_data}
        )
        
        return build_api_response(
            success=True,
            message="Representative updated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/representatives/{rep_id}", response_model=dict)
async def delete_representative(rep_id: str):
    """Delete a representative"""
    
    try:
        rep_collection = get_representative_collection()
        
        result = await rep_collection.delete_one({"_id": rep_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Representative not found")
        
        return build_api_response(
            success=True,
            message="Representative deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))