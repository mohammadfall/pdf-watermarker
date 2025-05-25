import streamlit as st
import os
import pandas as pd
import tempfile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from io import BytesIO

# إعداد الخط
FONT_PATH = "Cairo-Regular.ttf"
pdfmetrics.registerFont(TTFont("Cairo", FONT_PATH))

# إعداد Google Drive API
FOLDER_ID = "1TUZ_DMdU3e1LDLklCIQOUk-IkI1r1pxN"
SERVICE_ACCOUNT_FILE = "service_account.json"

def upload_to_drive(filename, filepath):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": filename,
        "parents": [FOLDER_ID]
    }
    media = MediaFileUpload(filepath, mimetype="application/pdf")
    service.files().create(body=file_metadata, media_body=media, fields="id").execute()

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

def process_and_upload(pdf_file, excel_file):
    df = pd.read_excel(excel_file)
    student_names = df[df.columns[0]].dropna().astype(str).tolist()

    # حفظ مؤقت للـ PDF الأساسي
    base_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    base_temp.write(pdf_file.read())
    base_temp.close()

    for name in student_names:
        st.write(f"🔄 جاري إنشاء ورفع ملف الطالب: {name}")
        reader = PdfReader(base_temp.name)
        writer = PdfWriter()
        watermark_page = create_watermark_page(name)

        for page in reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)

        safe_name = name.replace(" ", "_").replace("+", "plus")
        output_path = os.path.join(tempfile.gettempdir(), f"{safe_name}.pdf")
        with open(output_path, "wb") as f_out:
            writer.write(f_out)

        upload_to_drive(f"{name}.pdf", output_path)

# واجهة Streamlit
st.set_page_config(page_title="PDF Uploader to Drive")
st.title("🚀 PDF Watermarker + Drive Uploader")

st.markdown("ارفع ملف PDF الأساسي وملف Excel يحتوي على أسماء الطلاب، وسيتم رفع ملفات PDF مباشرة إلى Google Drive داخل مجلدك الخاص.")

pdf_file = st.file_uploader("📄 ملف PDF الأساسي", type=["pdf"])
excel_file = st.file_uploader("📋 ملف Excel بالأسماء", type=["xlsx"])

if pdf_file and excel_file:
    if st.button("🚀 بدء التوليد والرفع"):
        with st.spinner("⏳ جاري التنفيذ..."):
            process_and_upload(pdf_file, excel_file)
            st.success("✅ تم رفع جميع الملفات بنجاح إلى Google Drive!")
