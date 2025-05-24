import streamlit as st
import tempfile
import os
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
st.markdown("قم برفع ملف PDF، ثم أدخل اسم الطالب لإضافة علامة مائية.")

# تحميل الخط
FONT_PATH = "Cairo-Regular.ttf"
pdfmetrics.registerFont(TTFont("Cairo", FONT_PATH))

def create_watermark(student_name: str) -> BytesIO:
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Cairo", 24)
    can.saveState()
    can.translate(10 * cm, 15 * cm)
    can.rotate(30)
    can.drawCentredString(0, 0, student_name)
    can.restoreState()
    can.save()
    packet.seek(0)
    return packet

def add_watermark(input_pdf, student_name):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    watermark_stream = create_watermark(student_name)
    watermark_pdf = PdfReader(watermark_stream)
    watermark_page = watermark_pdf.pages[0]

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    with open(temp_output.name, "wb") as f_out:
        writer.write(f_out)
    return temp_output.name

uploaded_file = st.file_uploader("📄 ارفع ملف PDF", type=["pdf"])
student_name = st.text_input("✍️ اسم الطالب (عربي أو إنجليزي)")

if uploaded_file and student_name:
    if st.button("🚀 إنشاء PDF بعلامة مائية"):
        with st.spinner("جاري المعالجة..."):
            watermarked_path = add_watermark(uploaded_file, student_name)
            with open(watermarked_path, "rb") as file:
                st.download_button("📥 تحميل الملف المعدل", file.read(), file_name=f"{student_name}.pdf")
            os.remove(watermarked_path)