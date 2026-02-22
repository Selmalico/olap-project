from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import QueryRequest, QueryResponse, ExportRequest, EmailRequest
from orchestrator.planner import plan_and_execute
from tools.duckdb_executor import get_schema_info
import uvicorn

app = FastAPI(
    title="OLAP BI Platform API",
    version="1.0.0",
    description="AI-powered OLAP Business Intelligence Platform with 7 agents"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to CloudFront domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/schema")
def get_schema():
    """Returns the data schema for the frontend Schema Explorer."""
    return get_schema_info()


@app.post("/query")
async def query(request: QueryRequest):
    """Main OLAP query endpoint. Routes through 7-agent planner."""
    try:
        result = plan_and_execute(
            query=request.query,
            history=request.history or [],
            conversation_id=request.conversation_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/pdf")
async def export_pdf(request: ExportRequest):
    """Generate PDF report and return presigned S3 download URL."""
    try:
        from tools.pdf_generator import generate_pdf
        from tools.s3_client import upload_pdf_get_url
        pdf_bytes = generate_pdf(request)
        url = upload_pdf_get_url(pdf_bytes, request.conversation_id)
        return {"download_url": url, "expires_in": "1 hour"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/email/send")
async def send_email(request: EmailRequest):
    """Generate PDF and email it via AWS SES."""
    try:
        from tools.pdf_generator import generate_pdf
        from tools.email_sender import send_report_email
        pdf_bytes = generate_pdf(request)
        send_report_email(
            to_email=request.to_email,
            subject=request.subject,
            pdf_bytes=pdf_bytes,
            query=request.query
        )
        return {"status": "sent", "to": request.to_email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
