from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import AuthenticatedUser, get_current_user
from app.repositories.company_repository import CompanyRepository
from app.schemas.common import ApiResponse
from app.services.rag_service import Citation, RAGService

router = APIRouter(prefix="/ask", tags=["RAG & Q&A"])


class AskQuestionRequest(BaseModel):
    company_id: UUID = Field(..., description="Target corporate entity ID")
    question: str = Field(..., min_length=1, max_length=1000, description="Forensic inquiry question")
    company_name: Optional[str] = Field(default=None, description="Optional target company name")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of evidence chunks to retrieve")


class AskQuestionResponse(BaseModel):
    answer: str = Field(..., description="Grounded AI response summary")
    company_name: str = Field(..., description="Target company name")
    company_id: str = Field(..., description="Target company ID")
    citations: List[Citation] = Field(default_factory=list, description="Evidence citations mapping")
    evidence_count: int = Field(default=0, description="Number of supporting evidence chunks used")


@router.post(
    "",
    response_model=ApiResponse[AskQuestionResponse],
    status_code=status.HTTP_200_OK,
    summary="Ask Evidence-Grounded Corporate Question",
    description="Query stored company research evidence using company-isolated pgvector similarity search.",
)
@limiter.limit(settings.ASK_RATE_LIMIT)
async def ask_company_question(
    request: Request,
    payload: AskQuestionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse[AskQuestionResponse]:

    clean_question = payload.question.strip()
    if not clean_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question text cannot be empty.",
        )

    company_repo = CompanyRepository()
    company = company_repo.get_by_id(payload.company_id)
    company_name = payload.company_name or (company["name"] if company else "Target Company")

    rag_service = RAGService()
    rag_res = rag_service.answer_question(
        company_id=payload.company_id,
        company_name=company_name,
        question=clean_question,
        top_k=payload.top_k,
    )

    response_data = AskQuestionResponse(
        answer=rag_res.answer,
        company_name=rag_res.company_name,
        company_id=rag_res.company_id,
        citations=rag_res.citations,
        evidence_count=rag_res.evidence_count,
    )

    return ApiResponse(data=response_data)
