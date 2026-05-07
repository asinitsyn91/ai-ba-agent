from pydantic import BaseModel
from typing import Optional, Any


class AnalyzeRequest(BaseModel):
    text: str
    project_name: Optional[str] = "tbd"


class ClarifyRequest(BaseModel):
    session_id: str
    answers: str


class FinalizeRequest(BaseModel):
    session_id: str


class RequirementItem(BaseModel):
    req_id: str
    req_type: str
    ears_pattern: Optional[str] = None
    description: str
    rationale: Optional[str] = None
    source: Optional[str] = None
    originator: Optional[str] = None
    fit_criterion: Optional[str] = None
    priority: Optional[str] = "tbd"
    conflicts: Optional[list] = []
    status: Optional[str] = "extracted"
    notes: Optional[str] = None


class PipelineResponse(BaseModel):
    session_id: str
    project_name: str
    language: str
    requirements: list[RequirementItem]
    quality_check: dict
    questions: list[dict]
    status: str  # needs_clarification | ready


class FinalizeResponse(BaseModel):
    session_id: str
    volere_json: dict
    summary: dict
