from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    AnalyzeRequest, ClarifyRequest, FinalizeRequest,
    PipelineResponse, FinalizeResponse
)
from app.services.pipeline import PipelineService
from app.services.session_store import create_session, get_session, update_session

router = APIRouter(prefix="/api/v1", tags=["pipeline"])
svc = PipelineService()


@router.post("/analyze", response_model=PipelineResponse)
def analyze(req: AnalyzeRequest):
    """Stage 1-5: Extract, classify, normalize, quality-check, generate questions."""
    result = svc.run_full_pipeline(req.text, req.project_name)
    sid = create_session(result)
    return PipelineResponse(
        session_id=sid,
        project_name=result["project_name"],
        language=result["language"],
        requirements=result["requirements"],
        quality_check=result["quality_check"],
        questions=result["questions"],
        status=result["status"],
    )


@router.post("/clarify", response_model=PipelineResponse)
def clarify(req: ClarifyRequest):
    """Apply user answers to clarification questions and update requirements."""
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    updated_reqs = svc.apply_clarifications(req.answers, session["requirements"])

    # Re-run quality check on updated requirements
    quality = svc.run_stage4(updated_reqs)
    questions_result = svc.run_stage5(updated_reqs, quality)

    session.update({
        "requirements": updated_reqs,
        "quality_check": quality,
        "questions": questions_result.get("questions", []),
        "status": "needs_clarification" if questions_result.get("questions") else "ready",
    })
    update_session(req.session_id, session)

    return PipelineResponse(
        session_id=req.session_id,
        project_name=session["project_name"],
        language=session["language"],
        requirements=updated_reqs,
        quality_check=quality,
        questions=questions_result.get("questions", []),
        status=session["status"],
    )


@router.post("/finalize", response_model=FinalizeResponse)
def finalize(req: FinalizeRequest):
    """Stage 6: Generate final Volere JSON document."""
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    volere_json = svc.run_stage6(
        session["requirements"],
        session["quality_check"],
        session["project_name"],
    )

    reqs = session["requirements"]
    by_type: dict = {}
    for r in reqs:
        t = r.get("req_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    summary = {
        "total": len(reqs),
        "by_type": by_type,
        "open_questions": len(session.get("questions", [])),
        "quality_issues": len(session.get("quality_check", {}).get("quality_issues", [])),
        "conflicts": len(session.get("quality_check", {}).get("conflicts", [])),
        "gaps": session.get("quality_check", {}).get("gaps", []),
    }

    return FinalizeResponse(
        session_id=req.session_id,
        volere_json=volere_json,
        summary=summary,
    )


@router.get("/session/{session_id}")
def get_session_data(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/health")
def health():
    return {"status": "ok"}
