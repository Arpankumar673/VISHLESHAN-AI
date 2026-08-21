from langgraph.graph import END, StateGraph
from app.research.graph.nodes import (
    node_company_research,
    node_evidence_trust,
    node_news_hiring,
    node_persist_results,
    node_report_agent,
    node_resolve_identity,
    node_risk_analysis,
    node_technology_reputation,
    node_verification,
)
from app.research.graph.state import ResearchGraphState


def create_research_graph() -> StateGraph:
    """
    Constructs and compiles the Vishleshan AI multi-agent research workflow graph.
    Structure:
    1. node_resolve_identity (Stage 1)
    2. Parallel Fan-Out (Stage 2):
       - node_company_research
       - node_verification
       - node_news_hiring
       - node_technology_reputation
    3. Fan-In to node_risk_analysis (Stage 3)
    4. node_evidence_trust (Stage 4)
    5. node_report_agent (Stage 5)
    6. node_persist_results (Stage 6)
    """
    workflow = StateGraph(ResearchGraphState)

    # Register Nodes
    workflow.add_node("resolve_identity", node_resolve_identity)
    workflow.add_node("company_research", node_company_research)
    workflow.add_node("verification", node_verification)
    workflow.add_node("news_hiring", node_news_hiring)
    workflow.add_node("technology_reputation", node_technology_reputation)
    workflow.add_node("risk_analysis", node_risk_analysis)
    workflow.add_node("evidence_trust", node_evidence_trust)
    workflow.add_node("report_agent", node_report_agent)
    workflow.add_node("persist_results", node_persist_results)

    # Set Entry Point
    workflow.set_entry_point("resolve_identity")

    # Parallel Fan-Out Edges from resolve_identity to 4 independent research branches
    workflow.add_edge("resolve_identity", "company_research")
    workflow.add_edge("resolve_identity", "verification")
    workflow.add_edge("resolve_identity", "news_hiring")
    workflow.add_edge("resolve_identity", "technology_reputation")

    # Fan-In Edges from 4 independent research branches to risk_analysis
    workflow.add_edge("company_research", "risk_analysis")
    workflow.add_edge("verification", "risk_analysis")
    workflow.add_edge("news_hiring", "risk_analysis")
    workflow.add_edge("technology_reputation", "risk_analysis")

    # Sequential Synthesis Pipeline
    workflow.add_edge("risk_analysis", "evidence_trust")
    workflow.add_edge("evidence_trust", "report_agent")
    workflow.add_edge("report_agent", "persist_results")
    workflow.add_edge("persist_results", END)

    return workflow.compile()


# Compiled Singleton Graph Instance
research_graph = create_research_graph()
