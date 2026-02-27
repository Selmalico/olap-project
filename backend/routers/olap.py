"""
Direct OLAP operation endpoints (structured, no natural language).
Useful for the frontend's OLAP control panel.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.anomaly_detection import AnomalyDetectionAgent
from agents.cube_operations import CubeOperationsAgent
from agents.dimension_navigator import DimensionNavigatorAgent
from agents.executive_summary import ExecutiveSummaryAgent
from agents.kpi_calculator import KPICalculatorAgent
from agents.report_generator import ReportGeneratorAgent
from agents.visualization_agent import VisualizationAgent
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils import sanitize

router = APIRouter(prefix="/api/olap", tags=["OLAP Operations"])

_cube = CubeOperationsAgent()
_nav = DimensionNavigatorAgent()
_kpi = KPICalculatorAgent()
_rpt = ReportGeneratorAgent()
_anomaly = AnomalyDetectionAgent()
_exec_summary = ExecutiveSummaryAgent()
_viz = VisualizationAgent()


# ── Pydantic models ───────────────────────────────────────────────────────────


class DrillRequest(BaseModel):
    hierarchy: str
    from_level: str
    to_level: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class SliceRequest(BaseModel):
    dimension: str
    value: Any
    group_by: Optional[List[str]] = None
    measures: Optional[List[str]] = None


class DiceRequest(BaseModel):
    filters: Dict[str, Any]
    group_by: Optional[List[str]] = None
    measures: Optional[List[str]] = None


class PivotRequest(BaseModel):
    rows: str
    columns: str
    values: str = "revenue"
    filters: Optional[Dict[str, Any]] = None
    top_n: Optional[int] = None


class YoYRequest(BaseModel):
    measure: str = "revenue"
    group_by: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class MoMRequest(BaseModel):
    measure: str = "revenue"
    year: Optional[int] = None
    filters: Optional[Dict[str, Any]] = None


class MarginsRequest(BaseModel):
    group_by: str = "category"
    filters: Optional[Dict[str, Any]] = None
    sort_desc: bool = True


class TopNRequest(BaseModel):
    measure: str = "revenue"
    n: int = 5
    group_by: str = "country"
    filters: Optional[Dict[str, Any]] = None
    ascending: bool = False


class CompareRequest(BaseModel):
    period_a: Dict[str, Any]
    period_b: Dict[str, Any]
    measure: str = "revenue"
    group_by: Optional[str] = None


class ShareRequest(BaseModel):
    group_by: str = "region"
    filters: Optional[Dict[str, Any]] = None


def _olap_response(result: dict, add_totals: bool = True) -> dict:
    """Build response dict with enrichment from anomaly, visualization, and summary agents."""
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    try:
        report = _rpt.generate_table(result, add_totals=add_totals)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Report generation failed.", "error": str(e)},
        )

    # Enrich with anomaly detection
    try:
        rows = result.get("rows", [])
        if rows:
            anomalies_info = _anomaly.detect(rows)
            result["anomalies"] = anomalies_info.get("anomalies", [])
            result["flagged_rows"] = anomalies_info.get("flagged_rows", [])
    except Exception:
        pass

    # Enrich with visualization recommendation
    try:
        viz_config = _viz.recommend(result)
        result["chart_config"] = viz_config
    except Exception:
        pass

    # Enrich with executive summary
    try:
        summary_data = _exec_summary.summarize(result)
        result["executive_summary"] = summary_data.get("narrative", "")
    except Exception:
        pass

    return sanitize({"data": result, "report": report})


# ── Dimension Navigator ───────────────────────────────────────────────────────


@router.post(
    "/drill-down",
    responses={
        200: {"description": "Success. Returns data (agent result) and report."},
        400: {"description": "Bad request (e.g. invalid hierarchy or level)."},
        500: {"description": "Server error."},
    },
)
async def drill_down(body: DrillRequest) -> dict[str, Any]:
    """Drill down to a finer hierarchy level."""
    result = _nav.drill_down(
        body.hierarchy, body.from_level, body.to_level, body.filters
    )
    return JSONResponse(content=_olap_response(result))


@router.post("/roll-up")
async def roll_up(body: DrillRequest) -> dict[str, Any]:
    """Roll up to a coarser hierarchy level."""
    result = _nav.roll_up(body.hierarchy, body.from_level, body.to_level, body.filters)
    return JSONResponse(content=_olap_response(result))


@router.get("/hierarchies")
async def get_hierarchies() -> dict[str, Any]:
    """Return available dimension hierarchies."""
    return JSONResponse(content=sanitize(_nav.get_hierarchy_info()))


# ── Cube Operations ───────────────────────────────────────────────────────────


@router.post(
    "/slice",
    responses={
        200: {"description": "Success. Returns data and report."},
        400: {"description": "Bad request (e.g. unknown dimension)."},
        500: {"description": "Server error."},
    },
)
async def slice_cube(body: SliceRequest) -> dict[str, Any]:
    """Slice the cube on a single dimension."""
    result = _cube.slice(body.dimension, body.value, body.group_by, body.measures)
    return JSONResponse(content=_olap_response(result))


@router.post("/dice")
async def dice_cube(body: DiceRequest) -> dict[str, Any]:
    """Dice the cube with multiple dimension filters."""
    result = _cube.dice(body.filters, body.group_by, body.measures)
    return JSONResponse(content=_olap_response(result))


@router.post("/pivot")
async def pivot_cube(body: PivotRequest) -> dict[str, Any]:
    """Pivot the cube across two dimensions."""
    result = _cube.pivot(body.rows, body.columns, body.values, body.filters, body.top_n)
    return JSONResponse(content=_olap_response(result, add_totals=False))


@router.get("/dimensions/{dimension}/values")
async def dimension_values(dimension: str) -> dict[str, Any]:
    """Get all distinct values for a dimension."""
    result = _cube.get_dimension_values(dimension)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return JSONResponse(content=sanitize(result))


# ── KPI Calculator ────────────────────────────────────────────────────────────


def _kpi_response(result: dict) -> dict:
    """Build KPI response with report and summary; raise 400 if agent error."""
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    try:
        report = _rpt.generate_table(result)
        summary = _rpt.executive_summary(result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Report/summary generation failed.", "error": str(e)},
        )
    return sanitize({"data": result, "report": report, "summary": summary})


@router.post("/kpi/yoy-growth")
async def yoy_growth(body: YoYRequest) -> dict[str, Any]:
    """Year-over-year growth analysis."""
    result = _kpi.yoy_growth(body.measure, body.group_by, body.filters)
    return JSONResponse(content=_kpi_response(result))


@router.post("/kpi/mom-change")
async def mom_change(body: MoMRequest) -> dict[str, Any]:
    """Month-over-month change analysis."""
    result = _kpi.mom_change(body.measure, body.year, body.filters)
    return JSONResponse(content=_kpi_response(result))


@router.post("/kpi/margins")
async def profit_margins(body: MarginsRequest) -> dict[str, Any]:
    """Profit margin analysis by dimension."""
    result = _kpi.profit_margins(body.group_by, body.filters, body.sort_desc)
    return JSONResponse(content=_kpi_response(result))


@router.post("/kpi/top-n")
async def top_n(body: TopNRequest) -> dict[str, Any]:
    """Top N ranking by measure."""
    result = _kpi.top_n(
        body.measure, body.n, body.group_by, body.filters, body.ascending
    )
    return JSONResponse(content=_kpi_response(result))


@router.post("/kpi/compare")
async def compare_periods(body: CompareRequest) -> dict[str, Any]:
    """Compare two time periods."""
    result = _kpi.compare_periods(
        body.period_a, body.period_b, body.measure, body.group_by
    )


@router.post("/kpi/revenue-share")
async def revenue_share(body: ShareRequest) -> dict[str, Any]:
    """Revenue share by dimension."""
    result = _kpi.revenue_share(body.group_by, body.filters)
    return JSONResponse(content=_kpi_response(result))
