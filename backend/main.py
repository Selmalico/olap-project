import threading
import time

import uvicorn
from database.connection import init_db
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import EmailRequest, ExportRequest
from routers import olap as olap_router
from routers import query as query_router
from tools.duckdb_executor import get_schema_info

app = FastAPI(
    title="OLAP BI Platform API",
    version="2.0.0",
    description="Multi-Agent OLAP Business Intelligence Platform — 7 specialist agents",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to CloudFront domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers
app.include_router(query_router.router)
app.include_router(olap_router.router)

# Global flag to track if DB is ready
_db_initialized = False


def _init_db_background():
    """Initialize database in background thread to not block startup."""
    global _db_initialized
    try:
        print("[INFO] Starting database initialization in background...")
        init_db()
        _db_initialized = True
        print("[OK] Database initialization complete")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        _db_initialized = False


@app.on_event("startup")
def startup():
    """Start database initialization in background thread."""
    print("[INFO] Backend startup event triggered")
    # Run DB init in background so API responds immediately
    db_thread = threading.Thread(target=_init_db_background, daemon=True)
    db_thread.start()
    print("[INFO] Database initialization started in background thread")


@app.get("/health")
def health_check():
    """Health check endpoint - returns immediately."""
    return {"status": "ok", "version": "2.0.0", "database_ready": _db_initialized}


@app.get("/schema")
def get_schema():
    """Returns the data schema for the frontend Schema Explorer."""
    try:
        return get_schema_info()
    except Exception:
        # Fallback static schema when S3/config not available
        return {
            "fact_table": "fact_sales",
            "dimensions": [
                "year",
                "quarter",
                "month",
                "month_name",
                "region",
                "country",
                "category",
                "subcategory",
                "customer_segment",
            ],
            "measures": ["revenue", "profit", "cost", "quantity", "profit_margin"],
            "date_range": "2022-2024",
        }


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
        from tools.email_sender import send_report_email
        from tools.pdf_generator import generate_pdf

        pdf_bytes = generate_pdf(request)
        send_report_email(
            to_email=request.to_email,
            subject=request.subject,
            pdf_bytes=pdf_bytes,
            query=request.query,
        )
        return {"status": "sent", "to": request.to_email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


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
        from tools.email_sender import send_report_email
        from tools.pdf_generator import generate_pdf

        pdf_bytes = generate_pdf(request)
        send_report_email(
            to_email=request.to_email,
            subject=request.subject,
            pdf_bytes=pdf_bytes,
            query=request.query,
        )
        return {"status": "sent", "to": request.to_email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
