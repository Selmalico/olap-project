import boto3
from config import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime


def send_report_email(to_email: str, subject: str, pdf_bytes: bytes, query: str):
    ses = boto3.client("ses", region_name=settings.aws_region)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = settings.ses_sender_email
    msg["To"] = to_email

    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #222; padding: 24px;">
      <div style="border-bottom: 3px solid #2E75B6; padding-bottom: 12px; margin-bottom: 20px;">
        <h2 style="color: #1E3A5F; margin: 0;">Your OLAP Analysis Report</h2>
      </div>
      <p>Your requested analysis report is attached as a PDF.</p>
      <div style="background: #EBF3FB; border-left: 4px solid #2E75B6;
                  padding: 12px 16px; margin: 16px 0; border-radius: 2px;">
        <strong>Query:</strong> {query}
      </div>
      <p style="color: #888; font-size: 12px;">
        Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
      </p>
      <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
      <p style="color: #aaa; font-size: 11px;">OLAP BI Platform -- Automated Report</p>
    </body></html>
    """

    msg.attach(MIMEText(html_body, "html"))

    pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_part.add_header(
        "Content-Disposition", "attachment",
        filename=f"olap_report_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.pdf"
    )
    msg.attach(pdf_part)

    ses.send_raw_email(
        Source=settings.ses_sender_email,
        Destinations=[to_email],
        RawMessage={"Data": msg.as_string()}
    )
