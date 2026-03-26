# from pydantic import BaseModel, Field, HttpUrl
# from typing import Optional, List, Dict, Any
# from datetime import datetime
# from enum import Enum


# # Enums
# class PersonalityType(str, Enum):
#     ANGRY = "angry"
#     ARROGANT = "arrogant"
#     SOFT = "soft"
#     COLD_HEARTED = "cold_hearted"
#     NICE = "nice"
#     COOL = "cool"
#     NOT_WELL = "not_well"
#     ANALYTICAL = "analytical"


# class RoleType(str, Enum):
#     CEO = "ceo"
#     CMO = "cmo"
#     CFO = "cfo"
#     COO = "coo"
#     CTO = "cto"
#     VP_SALES = "vp_sales"
#     DIRECTOR = "director"
#     MANAGER = "manager"


# class DifficultyLevel(str, Enum):
#     BEGINNER = "beginner"
#     INTERMEDIATE = "intermediate"
#     ADVANCED = "advanced"


# class MeetingMode(str, Enum):
#     ONE_TO_ONE = "1-on-1"
#     ONE_TO_TWO = "1-on-2"
#     ONE_TO_THREE = "1-on-3"


# # Sales Person Schemas
# class ProductMaterial(BaseModel):
#     file_name: str
#     file_url: str  # S3 URL
#     file_type: str  # pdf, pptx, doc, image


# class SalespersonCreate(BaseModel):
#     product_name: str
#     product_url: Optional[HttpUrl] = None
#     description: str
#     # materials: Optional[List[ProductMaterial]] = []


# class SalespersonResponse(BaseModel):
#     # id: str
#     # product_name: str
#     # product_url: Optional[str] = None
#     # description: str
#     # materials: List[ProductMaterial]
#     # created_at: datetime
#     id: str
#     product_name: str
#     product_url: Optional[str] = None
#     description: str
#     materials: List[ProductMaterial] = []  # S3 upload এর পরে populate হবে
#     created_at: datetime


# # Company Schemas
# class CompanyData(BaseModel):
#     company_size: Optional[str] = None
#     headquarters: Optional[str] = None
#     revenue: Optional[str] = None
#     industry: Optional[str] = None
#     tech_stack: Optional[List[str]] = []
#     open_positions: Optional[int] = None
#     customer_reviews: Optional[Dict[str, Any]] = None
#     latest_news: Optional[List[str]] = []
#     financial_growth: Optional[str] = None


# class CompanyCreate(BaseModel):
#     company_url: HttpUrl
#     auto_fetch: bool = True  # Auto fetch data from website


# class CompanyResponse(BaseModel):
#     id: str
#     company_url: str
#     company_data: CompanyData
#     created_at: datetime
#     last_updated: datetime


# # Representative Schemas
# class RepresentativeCreate(BaseModel):
#     name: str
#     role: RoleType
#     tenure_months: int
#     personality_traits: List[PersonalityType]
#     is_decision_maker: bool = False
#     linkedin_profile: Optional[HttpUrl] = None
#     notes: Optional[str] = None
#     voice_id: Optional[str] = None  # ElevenLabs voice ID


# class RepresentativeResponse(BaseModel):
#     id: str
#     name: str
#     role: str
#     tenure_months: int
#     personality_traits: List[str]
#     is_decision_maker: bool
#     linkedin_profile: Optional[str]
#     notes: Optional[str]
#     voice_id: Optional[str]


# # Meeting Schemas
# class MeetingCreate(BaseModel):
#     salesperson_id: str
#     company_id: str
#     meeting_mode: MeetingMode
#     representatives: List[str]  # List of representative IDs
#     meeting_goal: str
#     personality: PersonalityType = PersonalityType.NICE
#     duration_minutes: int = 30
#     difficulty: DifficultyLevel = DifficultyLevel.BEGINNER


# class MeetingResponse(BaseModel):
#     id: str
#     salesperson_id: str
#     company_id: str
#     meeting_mode: str
#     representatives: List[RepresentativeResponse]
#     meeting_goal: str
#     top_5_questions: List[str]
#     personality: str
#     duration_minutes: int
#     difficulty: str
#     status: str  # pending, active, completed
#     created_at: datetime


# # Conversation Schemas
# class ConversationTurn(BaseModel):
#     turn_number: int
#     speaker: str  # salesperson or rep_id
#     speaker_name: str
#     text: str
#     audio_url: Optional[str] = None  # S3 URL
#     timestamp: str  # HH:MM:SS
#     duration_seconds: float
#     created_at: datetime


# class ConversationCreate(BaseModel):
#     meeting_id: str
#     speaker: str
#     speaker_name: str
#     text: str
#     audio_data: Optional[bytes] = None


# class ConversationResponse(BaseModel):
#     id: str
#     meeting_id: str
#     turns: List[ConversationTurn]
#     total_turns: int
#     salesperson_talk_time: float
#     representatives_talk_time: float
#     total_duration: float


# # AI Response Schema
# class AIResponse(BaseModel):
#     speaker_id: str
#     speaker_name: str
#     response_text: str
#     audio_url: Optional[str] = None
#     should_interrupt: bool = False
#     confidence_score: float = 1.0







from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class PersonalityType(str, Enum):
    ANGRY = "angry"
    ARROGANT = "arrogant"
    SOFT = "soft"
    COLD_HEARTED = "cold_hearted"
    NICE = "nice"
    COOL = "cool"
    NOT_WELL = "not_well"
    ANALYTICAL = "analytical"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    DIRECT = "direct"


class RoleType(str, Enum):
    CEO = "ceo"
    CMO = "cmo"
    CFO = "cfo"
    COO = "coo"
    CTO = "cto"
    VP_SALES = "vp_sales"
    DIRECTOR = "director"
    MANAGER = "manager"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class MeetingMode(str, Enum):
    ONE_TO_ONE = "1-on-1"
    ONE_TO_TWO = "1-on-2"
    ONE_TO_THREE = "1-on-3"


class SalesMethodology(str, Enum):
    MEDDIC = "MEDDIC"
    CHALLENGER_SALES = "Challenger Sales"
    BANT = "BANT"
    SPIN_SELLING = "SPIN Selling"
    MEDDPICC = "MEDDPICC"
    VALUE_SELLING = "Value Selling"


# Sales Person Schemas
class ProductMaterial(BaseModel):
    file_name: str
    file_url: str
    file_type: str


class SalespersonCreate(BaseModel):
    product_name: str
    product_url: Optional[HttpUrl] = None
    description: str


class SalespersonResponse(BaseModel):
    id: str
    product_name: str
    product_url: Optional[str] = None
    description: str
    materials: List[ProductMaterial] = []
    created_at: datetime


# =========================
# ✅ UPDATED COMPANY SCHEMA
# =========================

class HiringData(BaseModel):
    open_positions: Optional[int] = None
    hiring_summary: Optional[str] = None


class CustomerReviews(BaseModel):
    rating: Optional[float] = None
    total_reviews: Optional[int] = None
    summary: Optional[str] = None


class FinancialStatements(BaseModel):
    yoy_growth: Optional[str] = None
    arr: Optional[str] = None
    burn_rate: Optional[str] = None


class ProductDocumentation(BaseModel):
    api_docs_available: Optional[bool] = None
    integration_guides_available: Optional[bool] = None
    video_tutorials_available: Optional[bool] = None
    documentation_url: Optional[HttpUrl] = None


class CompanyData(BaseModel):
    company_size: Optional[str] = None
    headquarters: Optional[str] = None
    revenue: Optional[str] = None
    industry: Optional[str] = None
    
    wappalyzer_tech_stack: Optional[List[str]] = []
    
    hiring_data: Optional[HiringData] = None
    customer_reviews: Optional[CustomerReviews] = None
    latest_news: Optional[List[str]] = []
    
    financial_statements: Optional[FinancialStatements] = None
    product_documentation: Optional[ProductDocumentation] = None


class CompanyCreate(BaseModel):
    company_url: HttpUrl
    auto_fetch: bool = True


class CompanyResponse(BaseModel):
    id: str
    company_url: str
    company_data: CompanyData
    created_at: datetime
    last_updated: datetime


# =========================
# Rest of file unchanged
# =========================

class RepresentativeCreate(BaseModel):
    name: str
    role: RoleType
    # tenure_months: int
    # personality_traits: List[PersonalityType]
    is_decision_maker: bool = False
    linkedin_profile: Optional[HttpUrl] = None
    notes: Optional[str] = None
    voice_id: Optional[str] = None


class RepresentativeResponse(BaseModel):
    id: str
    name: str
    role: str
    # tenure_months: int
    # personality_traits: List[str]
    is_decision_maker: bool
    linkedin_profile: Optional[str]
    notes: Optional[str]
    voice_id: Optional[str]


class MeetingCreate(BaseModel):
    salesperson_id: str
    company_id: str
    meeting_mode: MeetingMode
    representatives: List[str]
    meeting_goal: str
    personality: PersonalityType = PersonalityType.NICE
    duration_minutes: int = 30
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    sales_methodology: SalesMethodology = SalesMethodology.MEDDIC


class MeetingResponse(BaseModel):
    id: str
    salesperson_id: str
    company_id: str
    meeting_mode: str
    representatives: List[RepresentativeResponse]
    meeting_goal: str
    top_5_questions: List[str]
    personality: str
    duration_minutes: int
    difficulty: str
    sales_methodology: str
    status: str
    created_at: datetime


class ConversationTurn(BaseModel):
    turn_number: int
    speaker: str
    speaker_name: str
    text: str
    audio_url: Optional[str] = None
    timestamp: str
    duration_seconds: float
    created_at: datetime


class ConversationCreate(BaseModel):
    meeting_id: str
    speaker: str
    speaker_name: str
    text: str
    audio_data: Optional[bytes] = None


class ConversationResponse(BaseModel):
    id: str
    meeting_id: str
    turns: List[ConversationTurn]
    total_turns: int
    salesperson_talk_time: float
    representatives_talk_time: float
    total_duration: float
    recording_s3_url: Optional[str] = None  # Permanent S3 link, set after session ends


class AIResponse(BaseModel):
    speaker_id: str
    speaker_name: str
    response_text: str
    audio_url: Optional[str] = None
    should_interrupt: bool = False
    confidence_score: float = 1.0