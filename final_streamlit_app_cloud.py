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
from zipfile import ZipFile
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

FONT_PATH = "Cairo-Regular.ttf"
if not os.path.exists(FONT_PATH):
    import urllib.request
    url = "https://github.com/google/fonts/raw/main/ofl/cairo/Cairo-Regular.ttf"
    urllib.request.urlretrieve(url, FONT_PATH)

pdfmetrics.registerFont(TTFont("Cairo", FONT_PATH))

FOLDER_ID = "1TUZ_DMdU3e1LDLklCIQOUk-IkI1r1pxN"
service_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
creds = service_account.Credentials.from_service_account_info(
    service_info,
    scopes=["https://www.googleapis.com/auth/drive"]
)
drive_service = build("drive", "v3", credentials=creds)

def upload_to_drive(filename, filepath):
    file_metadata = {"name": filename, "parents": [FOLDER_ID]}
    media = MediaFileUpload(filepath, mimetype="application/pdf")
    drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

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

def generate_and_zip(base_pdf, excel_file):
    df = pd.read_excel(excel_file)
    names = df[df.columns[0]].dropna().astype(str).tolist()
    base_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    base_temp.write(base_pdf.read())
    base_temp.close()
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "watermarked_students.zip")
    pdf_paths = []

    for name in names:
        reader = PdfReader(base_temp.name)
        writer = PdfWriter()
        watermark_page = create_watermark_page(name)
        for page in reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)

        safe_name = name.replace(" ", "_")
        file_path = os.path.join(temp_dir, f"{safe_name}.pdf")
        with open(file_path, "wb") as f_out:
            writer.write(f_out)
        pdf_paths.append(file_path)

    with ZipFile(zip_path, "w") as zipf:
        for file_path in pdf_paths:
            zipf.write(file_path, arcname=os.path.basename(file_path))
    return zip_path

def generate_and_upload(base_pdf, excel_file):
    df = pd.read_excel(excel_file)
    names = df[df.columns[0]].dropna().astype(str).tolist()
    base_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    base_temp.write(base_pdf.read())
    base_temp.close()

    for name in names:
        st.write(f"⬆️ جاري رفع ملف الطالب: {name}")
        reader = PdfReader(base_temp.name)
        writer = PdfWriter()
        watermark_page = create_watermark_page(name)
        for page in reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)

        safe_name = name.replace(" ", "_")
        file_path = os.path.join(tempfile.gettempdir(), f"{safe_name}.pdf")
        with open(file_path, "wb") as f_out:
            writer.write(f_out)

        upload_to_drive(f"{name}.pdf", file_path)

st.set_page_config(page_title="Watermarker + Drive Uploader")
st.title("📄 Watermark PDF & Upload to Google Drive")
st.markdown("ارفع ملف PDF وExcel بالأسماء، واختر بين تحميل الملفات أو رفعها على Google Drive.")

pdf_file = st.file_uploader("📄 ملف PDF الأساسي", type=["pdf"])
excel_file = st.file_uploader("📋 ملف Excel يحتوي على الأسماء", type=["xlsx"])
option = st.radio("اختر طريقة الحصول على الملفات:", ["📦 تحميل مجلد مضغوط (ZIP)", "☁️ رفع إلى Google Drive"])

if pdf_file and excel_file:
    if st.button("🚀 بدء العملية"):
        with st.spinner("⏳ جاري المعالجة..."):
            if option.startswith("📦"):
                zip_file_path = generate_and_zip(pdf_file, excel_file)
                with open(zip_file_path, "rb") as f:
                    st.download_button("⬇️ تحميل الملفات كمجلد مضغوط", f.read(), file_name="watermarked_students.zip")
            else:
                generate_and_upload(pdf_file, excel_file)
                st.success("✅ تم رفع جميع الملفات بنجاح إلى Google Drive!")