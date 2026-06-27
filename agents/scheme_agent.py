"""
agents/scheme_agent.py
=========================
Government Scheme Agent: searches agricultural schemes, explains
eligibility, and suggests applicable programs.
"""

from __future__ import annotations

from agents.base_agent import AgentResponse, BaseAgent
from tools.scheme_tool import explain_eligibility, search_schemes


class GovernmentSchemeAgent(BaseAgent):
    name = "government_scheme_agent"
    description = (
        "Searches government agricultural schemes by keyword/state, and explains eligibility "
        "for a farmer's specific profile (land size, state, etc.)."
    )
    tools = ["knowledge_base.search_government_schemes"]

    def run(
        self,
        keyword: str | None = None,
        state: str | None = None,
        farmer_profile: dict | None = None,
        **_,
    ) -> AgentResponse:
        matches = search_schemes(keyword=keyword, state=state)

        if not matches:
            return AgentResponse(
                agent_name=self.name,
                recommendation="No matching government schemes found for this search.",
                confidence_score=40.0,
                factors_considered=[f"Searched with keyword='{keyword}', state='{state}'."],
                alternatives=[],
            )

        top = matches[0]
        factors = [
            f"Scheme matched: {top.scheme_name} ({top.relevance_note}).",
            f"Eligibility: {top.eligibility}",
            f"Benefits: {top.benefits}",
        ]

        if farmer_profile:
            factors.append(explain_eligibility(top.scheme_name, farmer_profile))

        recommendation = f"{top.scheme_name} -- {top.benefits}"
        if top.official_link:
            recommendation += f" (verify at: {top.official_link})"

        alternatives = [m.scheme_name for m in matches[1:4]]

        return AgentResponse(
            agent_name=self.name,
            recommendation=recommendation,
            confidence_score=72.0,
            factors_considered=factors,
            alternatives=alternatives,
            raw_data={"matches": [m.__dict__ for m in matches]},
        )
