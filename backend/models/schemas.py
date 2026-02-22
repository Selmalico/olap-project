from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    history: Optional[List[Dict]] = []


class AgentResult(BaseModel):
    agent_name: str
    data: Optional[List[Dict]] = None
    sql: Optional[str] = None
    chart_config: Optional[Dict] = None
    narrative: Optional[str] = None
    anomalies: Optional[List[str]] = None
    kpis: Optional[Dict] = None
    error: Optional[str] = None


class QueryResponse(BaseModel):
    conversation_id: str
    agents_used: List[str]
    results: List[Dict]
    executive_summary: Optional[str] = None
    follow_up_questions: List[str] = []


class ExportRequest(BaseModel):
    conversation_id: str
    results: List[Dict]
    query: str
    title: str = "OLAP Analysis Report"


class EmailRequest(BaseModel):
    to_email: str
    subject: str
    conversation_id: str
    results: List[Dict]
    query: str
