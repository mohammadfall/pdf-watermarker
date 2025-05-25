import streamlit as st
import tempfile
import os
import shutil
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from io import BytesIO
from zipfile import ZipFile

# إعداد الصفحة
st.set_page_config(page_title="PDF Watermarker by Alomari")
st.title("🎓 PDF Watermarker by Alomari")
st.markdown("ارفع ملف PDF وملف Excel يحتوي على أسماء الطلاب، وسيتم إنشاء ملفات PDF مخصصة داخل مجلد مضغوط.")

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

def generate_zip(base_pdf, excel_file):
    df = pd.read_excel(excel_file)
    col = df.columns[0]
    student_names = df[col].dropna().astype(str).tolist()

    # حفظ الملف الأساسي مؤقتاً لإعادة قراءته داخل اللوب
    base_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    base_temp.write(base_pdf.read())
    base_temp.close()

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "watermarked_students.zip")
    pdf_paths = []

    for name in student_names:
        st.write(f"⬇️ جاري إنشاء الملف للطالب: {name}")
        base_reader = PdfReader(base_temp.name)
        writer = PdfWriter()
        watermark_page = create_watermark_page(name)

        for page in base_reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)

        safe_name = name.replace(" ", "_").replace("+", "plus")
        pdf_path = os.path.join(temp_dir, f"{safe_name}.pdf")
        with open(pdf_path, "wb") as f_out:
            writer.write(f_out)
        pdf_paths.append(pdf_path)

    with ZipFile(zip_path, "w") as zipf:
        for file_path in pdf_paths:
            zipf.write(file_path, arcname=os.path.basename(file_path))

    return zip_path

# واجهة التطبيق
pdf_file = st.file_uploader("📄 ارفع ملف PDF الأساسي", type=["pdf"])
excel_file = st.file_uploader("📋 ارفع ملف Excel يحتوي على الأسماء", type=["xlsx"])

if pdf_file and excel_file:
    if st.button("🚀 إنشاء مجلد مضغوط للطلاب"):
        with st.spinner("⏳ جاري المعالجة..."):
            zip_file_path = generate_zip(pdf_file, excel_file)
            with open(zip_file_path, "rb") as zip_file:
                st.download_button("📦 تحميل الملفات جميعها (ZIP)", zip_file.read(), file_name="watermarked_students.zip")