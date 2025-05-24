import streamlit as st
import tempfile
import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from io import BytesIO

# إعداد الصفحة
st.set_page_config(page_title="PDF Watermarker by Alomari")
st.title("🎓 PDF Watermarker by Alomari")
st.markdown("ارفع ملف PDF الأساسي، وملف Excel يحتوي على أسماء الطلاب، وسينشئ التطبيق ملفات PDF مخصصة لكل طالب.")

# تحميل الخط
FONT_PATH = "Cairo-Regular.ttf"
pdfmetrics.registerFont(TTFont("Cairo", FONT_PATH))

def create_watermark_page(text, font_size=14, spacing=200, rotation=35, alpha=0.08):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    c.setFont("Cairo", font_size)
    c.setFillAlpha(alpha)
    width, height = letter
    for x in range(0, int(width), spacing):
        for y in range(0, int(height), spacing):
            c.saveState()
            c.translate(x, y)
            c.rotate(rotation)
            c.drawString(0, 0, f"خاص بـ {text}")
            c.restoreState()
    c.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]

def generate_pdfs(base_pdf, excel_file):
    df = pd.read_excel(excel_file)
    student_names = df.iloc[:, 0].dropna().tolist()
    output_files = []

    reader = PdfReader(base_pdf)
    for name in student_names:
        writer = PdfWriter()
        watermark_page = create_watermark_page(name)
        for page in reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)

        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{name}.pdf")
        with open(temp_output.name, "wb") as f_out:
            writer.write(f_out)
        output_files.append((name, temp_output.name))

    return output_files

# الواجهة
pdf_file = st.file_uploader("📄 ارفع ملف PDF الأساسي", type=["pdf"])
excel_file = st.file_uploader("📋 ارفع ملف Excel يحتوي على الأسماء", type=["xlsx"])

if pdf_file and excel_file:
    if st.button("🚀 إنشاء ملفات PDF للطلاب"):
        with st.spinner("جاري المعالجة..."):
            results = generate_pdfs(pdf_file, excel_file)
            for name, file_path in results:
                with open(file_path, "rb") as file:
                    st.download_button(f"📥 تحميل ملف: {name}", file.read(), file_name=f"{name}.pdf")
                os.remove(file_path)