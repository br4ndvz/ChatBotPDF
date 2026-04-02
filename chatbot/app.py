from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from docx import Document
from fpdf import FPDF
from PIL import Image
import requests
import os

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/archivos_bot'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def word_to_pdf(docx_path, pdf_path):
    doc = Document(docx_path)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for para in doc.paragraphs:
        # Esto limpia caracteres raros para evitar errores de codificación
        texto = para.text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=texto)
    pdf.output(pdf_path)

@app.route('/webhook', methods=['POST'])
def chatbot():
    resp = MessagingResponse()
    media_url = request.values.get('MediaUrl0')
    mime_type = request.values.get('MediaContentType0')
    
    if media_url:
        input_path = os.path.join(UPLOAD_FOLDER, "entrada")
        pdf_filename = "convertido.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
        
        try:
            # Descargar archivo
            r = requests.get(media_url)
            with open(input_path, 'wb') as f:
                f.write(r.content)

            # Convertir
            if 'officedocument.wordprocessingml.document' in mime_type:
                word_to_pdf(input_path, pdf_path)
            elif 'image/' in mime_type:
                img = Image.open(input_path).convert('RGB')
                img.save(pdf_path, "PDF")
            
            # Crear link público
            link = f"{request.host_url}download/{pdf_filename}"
            resp.message(f"✅ ¡Conversión exitosa!\nDescarga tu PDF aquí: {link}")
            
        except Exception as e:
            resp.message(f"❌ Error interno: {str(e)}")
    else:
        resp.message("¡Hola! Envíame un archivo Word o una Imagen para convertirlo.")
    
    return str(resp)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
