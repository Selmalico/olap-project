from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os

env = Environment(loader=FileSystemLoader(
    os.path.join(os.path.dirname(__file__), '..', 'templates')
))


def generate_pdf(request) -> bytes:
    template = env.get_template("report.html")
    sections = []

    for result in request.results:
        if not result.get("data"):
            continue
        data = result["data"]
        cols = list(data[0].keys()) if data else []
        sections.append({
            "title": result.get("agent_name", "").replace("_", " ").title(),
            "columns": cols,
            "data": data[:50],  # Cap at 50 rows for readability
            "anomalies": result.get("anomalies", [])
        })

    exec_summary = next(
        (r.get("narrative") for r in request.results
         if r.get("agent_name") == "executive_summary"),
        None
    )

    html_content = template.render(
        title=request.title,
        query=request.query,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        executive_summary=exec_summary,
        sections=sections
    )

    return HTML(string=html_content).write_pdf()
