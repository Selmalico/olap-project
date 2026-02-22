import boto3
from config import settings
from datetime import datetime


s3 = boto3.client("s3", region_name=settings.aws_region)


def upload_pdf_get_url(pdf_bytes: bytes, conversation_id: str) -> str:
    """Upload PDF to S3, return a 1-hour presigned download URL."""
    key = f"reports/{datetime.utcnow().strftime('%Y/%m/%d')}/{conversation_id}.pdf"

    s3.put_object(
        Bucket=settings.s3_reports_bucket,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf"
    )

    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_reports_bucket, "Key": key},
        ExpiresIn=3600
    )
    return url
