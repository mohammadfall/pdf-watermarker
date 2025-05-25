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
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# إعداد الصفحة
st.set_page_config(page_title="PDF Watermarker by Alomari")
st.title("🎓 PDF Watermarker by Alomari")
st.markdown("ارفع ملف PDF وملف Excel بالأسماء، ثم اختر طريقة استلام الملفات.")

# تحميل الخط
FONT_PATH = "Cairo-Regular.ttf"
pdfmetrics.registerFont(TTFont("Cairo", FONT_PATH))

# مصادقة Google Drive (مرة واحدة)
@st.cache_resource
def authenticate_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)

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

def generate_pdfs(base_pdf, excel_file, output_mode):
    df = pd.read_excel(excel_file)
    col = df.columns[0]
    student_names = df[col].dropna().astype(str).tolist()

    base_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    base_temp.write(base_pdf.read())
    base_temp.close()

    temp_dir = tempfile.mkdtemp()
    output_paths = []

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
        output_paths.append((name, pdf_path))

    if output_mode == "تحميل كمجلد مضغوط (ZIP)":
        zip_path = os.path.join(temp_dir, "watermarked_students.zip")
        with ZipFile(zip_path, "w") as zipf:
            for _, path in output_paths:
                zipf.write(path, arcname=os.path.basename(path))
        return "zip", zip_path

    elif output_mode == "رفع إلى Google Drive (خاص)":
        drive = authenticate_drive()
        uploaded = []
        for name, path in output_paths:
            file_drive = drive.CreateFile({
                "title": f"{name}.pdf",
                "parents": [{"id": "1TUZ_DMdU3e1LDLklCIQOUk-IkI1r1pxN"}]
            })
            file_drive.SetContentFile(path)
            file_drive.Upload()
            uploaded.append(f"✅ تم رفع ملف {name}")
        return "drive", uploaded

# الواجهة
pdf_file = st.file_uploader("📄 ارفع ملف PDF الأساسي", type=["pdf"])
excel_file = st.file_uploader("📋 ارفع ملف Excel يحتوي على الأسماء", type=["xlsx"])
output_mode = st.radio("📤 اختر طريقة استلام الملفات:", ["تحميل كمجلد مضغوط (ZIP)", "رفع إلى Google Drive (خاص)"])

if pdf_file and excel_file:
    if st.button("🚀 بدء التوليد"):
        with st.spinner("⏳ جاري إنشاء الملفات..."):
            mode, result = generate_pdfs(pdf_file, excel_file, output_mode)
            if mode == "zip":
                with open(result, "rb") as zip_file:
                    st.download_button("📦 تحميل الملفات كمجلد مضغوط", zip_file.read(), file_name="watermarked_students.zip")
            elif mode == "drive":
                for msg in result:
                    st.success(msg)