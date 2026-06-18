from __future__ import annotations

from dataclasses import replace

from .models import IntakeProfile, MissingInfoItem


class IntakeModule:
    def build_questions(self, profile: IntakeProfile) -> list[str]:
        questions: list[str] = []
        if not profile.income_sources:
            questions.append("What are Moshe's income sources and approximate timing?")
        if not profile.accounts:
            questions.append("Which accounts should be monitored?")
        if not profile.recurring_expenses:
            questions.append("What recurring expenses should be tracked?")
        if not profile.monthly_obligations:
            questions.append("What fixed monthly obligations should be included?")
        if profile.risk_tolerance is None:
            questions.append("What is Moshe's risk tolerance: low, medium, or high?")
        if profile.emergency_reserve_target is None:
            questions.append("What emergency reserve target should the planner use?")
        return questions

    def missing_information(self, profile: IntakeProfile) -> list[MissingInfoItem]:
        return [MissingInfoItem(text=q, reason="Required for planning") for q in self.build_questions(profile)]

    def with_defaults(self, profile: IntakeProfile) -> IntakeProfile:
        return replace(profile, reporting_preferences=profile.reporting_preferences or {})
