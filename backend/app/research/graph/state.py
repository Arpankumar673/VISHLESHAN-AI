from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from uuid import UUID
from app.research.models import IdentityResult, NormalizedEvidence


def add_evidence(left: Optional[List[NormalizedEvidence]], right: Optional[List[NormalizedEvidence]]) -> List[NormalizedEvidence]:
    """Reducer for appending evidence items across parallel branches."""
    return (left or []) + (right or [])


def add_findings(left: Optional[List[Dict[str, Any]]], right: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Reducer for appending findings across parallel branches."""
    return (left or []) + (right or [])


def add_strings(left: Optional[List[str]], right: Optional[List[str]]) -> List[str]:
    """Dedicated reducer for combining string warnings and errors across parallel branches."""
    return (left or []) + (right or [])


def update_agent_results(left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Reducer for dictionary merging of individual agent results."""
    res = dict(left or {})
    res.update(right or {})
    return res


class ResearchGraphState(TypedDict):
    """
    LangGraph State model for Vishleshan AI multi-agent research workflow.
    Uses explicit type-checked reducers for concurrent parallel branch aggregation.
    """
    # Immutable Run Inputs
    research_run_id: UUID
    company_id: UUID
    company_name: str
    company_url: Optional[str]
    correlation_id: Optional[str]

    # Shared Identity State
    identity: Optional[IdentityResult]
    identity_status: str  # "verified" | "unverified" | "unresolved"

    # Reducer-Accumulated Agent Execution State
    agent_results: Annotated[Dict[str, Any], update_agent_results]
    evidence: Annotated[List[NormalizedEvidence], add_evidence]
    findings: Annotated[List[Dict[str, Any]], add_findings]

    # Derived Synthesis State
    trust_score: Optional[Dict[str, Any]]
    risk_summary: Optional[Dict[str, Any]]
    report_content: Optional[Dict[str, Any]]
    report_id: Optional[UUID]

    # Audit Trail & Error Log (Uses Dedicated add_strings Reducer)
    warnings: Annotated[List[str], add_strings]
    errors: Annotated[List[str], add_strings]
    status: str  # "queued" | "running" | "completed" | "partial" | "failed"
