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
    """Extract JSON from LLM response robustly (handles markdown fences, extra text)."""
    raw = raw.strip()
    # Strip markdown fences
    if "```" in raw:
        import re
        m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
        if m:
            raw = m.group(1).strip()
    # Find first JSON object or array
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = raw.find(start_char)
        if start != -1:
            # Find matching closing bracket
            depth = 0
            in_str = False
            escape = False
            for i, ch in enumerate(raw[start:], start):
                if escape:
                    escape = False
                    continue
                if ch == '\\' and in_str:
                    escape = True
                    continue
                if ch == '"' and not escape:
                    in_str = not in_str
                    continue
                if in_str:
                    continue
                if ch == start_char:
                    depth += 1
                elif ch == end_char:
                    depth -= 1
                    if depth == 0:
                        candidate = raw[start:i+1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break
    # Last resort
    return json.loads(raw)


class PipelineService:
    """6-stage Volere/EARS/BABOK requirements extraction pipeline."""

    def run_stage1(self, text: str) -> dict:
        prompt = STAGE1_EXTRACT_PROMPT.format(text=text)
        raw = _call_llm(prompt)
        result = _parse_json(raw)
        if isinstance(result, list):
            result = {"candidates": result, "language": "ru"}
        return result

    def run_stage2(self, candidates: list) -> dict:
        prompt = STAGE2_CLASSIFY_PROMPT.format(
            candidates_json=json.dumps(candidates, ensure_ascii=False, indent=2)
        )
        raw = _call_llm(prompt)
        result = _parse_json(raw)
        if isinstance(result, list):
            result = {"classified": result}
        return result

    def run_stage3(self, classified: list, original_text: str) -> dict:
        prompt = STAGE3_NORMALIZE_PROMPT.format(
            classified_json=json.dumps(classified, ensure_ascii=False, indent=2),
            original_text=original_text,
        )
        raw = _call_llm(prompt)
        result = _parse_json(raw)
        if isinstance(result, list):
            result = {"requirements": result}
        return result

    def run_stage4(self, requirements: list) -> dict:
        prompt = STAGE4_QUALITY_PROMPT.format(
            requirements_json=json.dumps(requirements, ensure_ascii=False, indent=2)
        )
        raw = _call_llm(prompt)
        result = _parse_json(raw)
        if not isinstance(result, dict):
            result = {"quality_issues": [], "conflicts": [], "gaps": []}
        return result

    def run_stage5(self, requirements: list, quality_issues: dict) -> dict:
        prompt = STAGE5_QUESTIONS_PROMPT.format(
            requirements_json=json.dumps(requirements, ensure_ascii=False, indent=2),
            quality_issues_json=json.dumps(quality_issues, ensure_ascii=False, indent=2),
        )
        raw = _call_llm(prompt)
        result = _parse_json(raw)
        if isinstance(result, list):
            result = {"questions": result}
        return result

    def run_stage6(self, requirements: list, quality_issues: dict, project_name: str) -> dict:
        prompt = STAGE6_JSON_PROMPT.format(
            requirements_json=json.dumps(requirements, ensure_ascii=False, indent=2),
            quality_issues_json=json.dumps(quality_issues, ensure_ascii=False, indent=2),
            project_name=project_name,
        )
        raw = _call_llm(prompt)
        result = _parse_json(raw)
        if not isinstance(result, dict):
            result = {"error": "LLM returned unexpected format", "raw": str(result)}
        return result

    def apply_clarifications(self, answers: str, requirements: list) -> list:
        prompt = CLARIFICATION_PROMPT.format(
            answers=answers,
            requirements_json=json.dumps(requirements, ensure_ascii=False, indent=2),
        )
        raw = _call_llm(prompt)
        try:
            updated = _parse_json(raw)
        except Exception:
            logger.warning("apply_clarifications: failed to parse LLM response, returning original")
            return requirements

        # Normalize: LLM may return {"requirements": [...]} or a plain list
        if isinstance(updated, dict):
            updated = updated.get("requirements") or updated.get("updated") or []
        if not isinstance(updated, list):
            logger.warning("apply_clarifications: unexpected type %s, returning original", type(updated))
            return requirements

        # Merge updated items back
        updated_map = {r["req_id"]: r for r in updated if isinstance(r, dict) and "req_id" in r}
        return [
            updated_map.get(req["req_id"], req) for req in requirements
        ]

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
