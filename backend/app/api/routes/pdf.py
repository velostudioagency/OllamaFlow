from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.api.schemas import GeneratePdfRequest

router = APIRouter()


@router.post("/api/generate-pdf")
async def generate_pdf(request: GeneratePdfRequest):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                                leftMargin=0.75 * inch, rightMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)
        story = []
        for line in request.content.split("\n"):
            if not line.strip():
                story.append(Spacer(1, 6))
            else:
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, body_style))
        if not story:
            story = [Paragraph("Empty document", body_style)]
        doc.build(story)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="application/pdf",
                                 headers={"Content-Disposition": "attachment; filename=output.pdf"})
    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
