from fpdf import FPDF
from plotly.io import to_image
from io import BytesIO
import tempfile
import os
import re
 # Handle bold formatting in analysis (e.g. **bold text**)
def write_formatted_text(text, pdf):
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font("Arial", "B", 11)
            pdf.write(6, part[2:-2])  # Strip the **
        else:
            pdf.set_font("Arial", "", 11)
            pdf.write(6, part)
    pdf.ln(8)

def generate_pdf_report(user_query: str, analysis: str, fig) -> bytes:
    # Convert Plotly figure to PNG image bytes
    image_bytes = to_image(fig, format="png", width=1000, height=800)

    # Save image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
        tmp_img.write(image_bytes)
        tmp_img_path = tmp_img.name

    # Build PDF
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 10, "Sample Report", align="C")

    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, f"User Query:\n{user_query}")

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Analysis:")
    pdf.ln(8)


    for line in analysis.split('\n'):
        write_formatted_text(line, pdf)

    # Insert image
    pdf.image(tmp_img_path, x=10, w=180)
    os.remove(tmp_img_path)

    # Return as bytes
    return pdf.output(dest="S").encode("latin1", 'replace')
