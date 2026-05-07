import json
import logging
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm_factory import get_llm
from app.prompts.pipeline_prompts import (
    SYSTEM_PROMPT,
    STAGE1_EXTRACT_PROMPT,
    STAGE2_CLASSIFY_PROMPT,
    STAGE3_NORMALIZE_PROMPT,
    STAGE4_QUALITY_PROMPT,
    STAGE5_QUESTIONS_PROMPT,
    STAGE6_JSON_PROMPT,
    CLARIFICATION_PROMPT,
)

logger = logging.getLogger(__name__)


def _call_llm(prompt: str) -> str:
    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    return response.content


def _parse_json(raw: str) -> Any:
    """Extract JSON from LLM response (may contain markdown fences)."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        # skip first and last fence lines
        inner = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        raw = inner.strip()
    return json.loads(raw)


class PipelineService:
    """6-stage Volere/EARS/BABOK requirements extraction pipeline."""

    def run_stage1(self, text: str) -> dict:
        prompt = STAGE1_EXTRACT_PROMPT.format(text=text)
        raw = _call_llm(prompt)
        return _parse_json(raw)

    def run_stage2(self, candidates: list) -> dict:
        prompt = STAGE2_CLASSIFY_PROMPT.format(
            candidates_json=json.dumps(candidates, ensure_ascii=False, indent=2)
        )
        raw = _call_llm(prompt)
        return _parse_json(raw)

    def run_stage3(self, classified: list, original_text: str) -> dict:
        prompt = STAGE3_NORMALIZE_PROMPT.format(
            classified_json=json.dumps(classified, ensure_ascii=False, indent=2),
            original_text=original_text,
        )
        raw = _call_llm(prompt)
        return _parse_json(raw)

    def run_stage4(self, requirements: list) -> dict:
        prompt = STAGE4_QUALITY_PROMPT.format(
            requirements_json=json.dumps(requirements, ensure_ascii=False, indent=2)
        )
        raw = _call_llm(prompt)
        return _parse_json(raw)

    def run_stage5(self, requirements: list, quality_issues: dict) -> dict:
        prompt = STAGE5_QUESTIONS_PROMPT.format(
            requirements_json=json.dumps(requirements, ensure_ascii=False, indent=2),
            quality_issues_json=json.dumps(quality_issues, ensure_ascii=False, indent=2),
        )
        raw = _call_llm(prompt)
        return _parse_json(raw)

    def run_stage6(self, requirements: list, quality_issues: dict, project_name: str) -> dict:
        prompt = STAGE6_JSON_PROMPT.format(
            requirements_json=json.dumps(requirements, ensure_ascii=False, indent=2),
            quality_issues_json=json.dumps(quality_issues, ensure_ascii=False, indent=2),
            project_name=project_name,
        )
        raw = _call_llm(prompt)
        return _parse_json(raw)

    def apply_clarifications(self, answers: str, requirements: list) -> list:
        prompt = CLARIFICATION_PROMPT.format(
            answers=answers,
            requirements_json=json.dumps(requirements, ensure_ascii=False, indent=2),
        )
        raw = _call_llm(prompt)
        updated = _parse_json(raw)
        # Merge updated items back
        updated_map = {r["req_id"]: r for r in updated}
        merged = []
        for req in requirements:
            if req["req_id"] in updated_map:
                merged.append(updated_map[req["req_id"]])
            else:
                merged.append(req)
        return merged

    def run_full_pipeline(self, text: str, project_name: str = "tbd") -> dict:
        """Run stages 1-5. Stage 6 called separately after clarification."""
        logger.info("Stage 1: extracting candidates")
        stage1 = self.run_stage1(text)

        logger.info("Stage 2: classifying")
        stage2 = self.run_stage2(stage1.get("candidates", []))

        logger.info("Stage 3: normalizing (EARS/Volere)")
        stage3 = self.run_stage3(stage2.get("classified", []), text)

        requirements = stage3.get("requirements", [])

        logger.info("Stage 4: quality check (BABOK)")
        stage4 = self.run_stage4(requirements)

        logger.info("Stage 5: clarification questions")
        stage5 = self.run_stage5(requirements, stage4)

        return {
            "project_name": project_name,
            "language": stage1.get("language", "ru"),
            "candidates": stage1.get("candidates", []),
            "requirements": requirements,
            "quality_check": stage4,
            "questions": stage5.get("questions", []),
            "status": "needs_clarification" if stage5.get("questions") else "ready",
        }
