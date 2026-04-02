from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
import aspose.words as aw
from PIL import Image
import requests
import os

app = Flask(__name__)

# Directorio temporal para procesar (Render usa /tmp para archivos volátiles)
UPLOAD_FOLDER = '/tmp/archivos_bot'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/webhook', methods=['POST'])
def chatbot():
    resp = MessagingResponse()
    
    media_url = request.values.get('MediaUrl0')
    mime_type = request.values.get('MediaContentType0')
    media_size = int(request.values.get('MediaSize0', 0)) 
    limit_16mb = 16 * 1024 * 1024 

    if media_url:
        if media_size > limit_16mb:
            resp.message("❌ Error: El archivo excede los 16MB permitidos.")
            return str(resp)
        
        # 1. Definir rutas
        input_path = os.path.join(UPLOAD_FOLDER, "archivo_entrada")
        output_filename = "convertido.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        # 2. Descargar el archivo desde Twilio
        r = requests.get(media_url)
        with open(input_path, 'wb') as f:
            f.write(r.content)

        try:
            # 3. Lógica de Conversión según el tipo
            if 'officedocument.wordprocessingml.document' in mime_type:
                # Conversión de Word a PDF (Aspose funciona en Linux)
                doc = aw.Document(input_path)
                doc.save(pdf_path)
            
            elif 'image/' in mime_type:
                # Conversión de Imagen a PDF (Pillow)
                image = Image.open(input_path)
                if image.mode == 'RGBA':
                    image = image.convert('RGB')
                image.save(pdf_path, "PDF")
            
            else:
                resp.message("⚠️ Formato no soportado. Envía un .docx o una imagen.")
                return str(resp)

            # 4. Respuesta al usuario
            # IMPORTANTE: Twilio necesita una URL pública para enviar el PDF de vuelta.
            # En el plan gratuito de Render, puedes enviar un link de descarga:
            host = request.host_url # Obtiene la URL de tu server en Render
            download_link = f"{host}download/{output_filename}"
            
            msg = resp.message(f"✅ ¡Conversión exitosa! Puedes descargar tu PDF aquí (vence pronto):\n{download_link}")
            
        except Exception as e:
            resp.message(f"❌ Error al procesar: {str(e)}")
            print(f"Error: {e}")
            
    else:
        resp.message("¡Hola! Envíame un Word o una Imagen y la convertiré a PDF por ti.")

    return str(resp)

# Ruta para que el usuario pueda descargar el archivo convertido
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    # Usar el puerto que asigne Render o el 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)