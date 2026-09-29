from __future__ import annotations

import re
import unicodedata
from typing import Any

from job_mentor.matching.config import (
    CORE_KEYWORDS,
    FORMULATION_COMPOUNDING_KEYWORDS,
    GERMAN_KEYWORDS,
    MATERIALS_KEYWORDS,
    MATCH_THRESHOLDS,
    NEGATIVE_CONTEXT_KEYWORDS,
    POLYMER_KEYWORDS,
    PRODUCT_DEVELOPMENT_KEYWORDS,
    RELATED_ELASTOMER_RUBBER_KEYWORDS,
    RND_KEYWORDS,
    TITLE_WEIGHT,
)
from job_mentor.models.job import Job


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9 \-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class MatchResult:
    def __init__(self, score: float, category: str, reasons: list[str]):
        self.score = max(0.0, min(100.0, score))
        self.category = category
        self.reasons = reasons

    def as_dict(self) -> dict[str, Any]:
        return {"score": self.score, "category": self.category, "reasons": self.reasons}


class MatchingEngine:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.keyword_groups = {
            "core": CORE_KEYWORDS,
            "elastomer_rubber": RELATED_ELASTOMER_RUBBER_KEYWORDS,
            "polymer": POLYMER_KEYWORDS,
            "materials": MATERIALS_KEYWORDS,
            "product_development": PRODUCT_DEVELOPMENT_KEYWORDS,
            "rnd": RND_KEYWORDS,
            "formulation": FORMULATION_COMPOUNDING_KEYWORDS,
            "german": GERMAN_KEYWORDS,
        }

    def get_threshold_category(self, score: float) -> str:
        if score >= MATCH_THRESHOLDS["STRONG_MATCH"]:
            return "STRONG_MATCH"
        if score >= MATCH_THRESHOLDS["GOOD_MATCH"]:
            return "GOOD_MATCH"
        if score >= MATCH_THRESHOLDS["POSSIBLE_MATCH"]:
            return "POSSIBLE_MATCH"
        return "IRRELEVANT"

    def _find_matches(self, text: str, context: str = "title") -> tuple[float, list[str]]:
        normalized = normalize_text(text)
        if not normalized:
            return 0.0, []

        score = 0.0
        reasons: list[str] = []
        selected_keywords: list[str] = []

        for group_name, group in self.keyword_groups.items():
            matches: list[tuple[str, float]] = []
            for keyword, weight in group.items():
                if keyword not in normalized:
                    continue
                matches.append((keyword, float(weight)))

            matches.sort(key=lambda item: (-len(item[0]), item[0]))
            for keyword, weight in matches:
                if any(existing in keyword or keyword in existing for existing in selected_keywords):
                    if any(len(existing) >= len(keyword) for existing in selected_keywords if existing in keyword or keyword in existing):
                        continue
                    selected_keywords = [
                        existing
                        for existing in selected_keywords
                        if not (existing in keyword or keyword in existing)
                    ]

                selected_keywords.append(keyword)
                match_reason = self._build_reason(keyword, group_name, context)
                score += weight
                if match_reason and match_reason not in reasons:
                    reasons.append(match_reason)

        for phrase, penalty in NEGATIVE_CONTEXT_KEYWORDS.items():
            if phrase in normalized:
                score += float(penalty)

        if context == "title":
            score *= TITLE_WEIGHT["high"]
        elif context == "description":
            score *= TITLE_WEIGHT["low"]
        else:
            score *= TITLE_WEIGHT["medium"]

        if score < 0:
            score = 0.0
        return min(score, 100.0), reasons

    def _build_reason(self, keyword: str, group_name: str, context: str) -> str:
        clean_keyword = keyword.strip().lower()
        if group_name == "core":
            return f"Core elastomer/polymer keyword '{clean_keyword}' detected in {context}"
        if group_name == "elastomer_rubber":
            return f"Elastomer/rubber technical term '{clean_keyword}' detected in {context}"
        if group_name == "polymer":
            return f"Polymer term '{clean_keyword}' detected in {context}"
        if group_name == "materials":
            return f"Materials development term '{clean_keyword}' detected in {context}"
        if group_name == "product_development":
            return f"Product development context '{clean_keyword}' detected in {context}"
        if group_name == "rnd":
            return f"R&D context '{clean_keyword}' detected in {context}"
        if group_name == "formulation":
            return f"Formulation/compounding term '{clean_keyword}' detected in {context}"
        if group_name == "german":
            return f"German technical term '{clean_keyword}' detected in {context}"
        return f"Relevant keyword '{clean_keyword}' detected in {context}"

    def score_job(self, job: Job) -> MatchResult:
        title_text = job.title or ""
        description_text = job.description or ""
        company_text = job.company or ""
        location_text = job.location or ""

        title_score, title_reasons = self._find_matches(title_text, context="title")
        description_score, description_reasons = self._find_matches(description_text, context="description")
        company_score, company_reasons = self._find_matches(company_text, context="company")
        location_score, location_reasons = self._find_matches(location_text, context="location")

        total_score = title_score + description_score * 0.7 + company_score * 0.25 + location_score * 0.15

        reasons = []
        for group in (title_reasons, description_reasons, company_reasons, location_reasons):
            for reason in group:
                if reason not in reasons:
                    reasons.append(reason)

        if total_score < 40 and ("software engineer" in normalize_text(title_text + " " + description_text)):
            total_score = min(total_score, 30)

        category = self.get_threshold_category(total_score)
        job.match_score = round(total_score, 2)
        job.match_reasons = reasons
        job.status = category
        return MatchResult(job.match_score, category, reasons)

    def filter_report_jobs(self, jobs: list[Job], minimum_score: int = 40) -> list[Job]:
        filtered = []
        for job in jobs:
            score = job.match_score
            if score >= minimum_score:
                filtered.append(job)
        return filtered
