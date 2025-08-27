import os
import re
from flask import Flask, send_file, render_template, jsonify
from pdf2image import convert_from_path
import pytesseract
import pandas as pd
from datetime import datetime
import io

app = Flask(__name__)

PDF_PATH = "/home/abraham/Escritorio/readPDF/file.pdf"  # Fixed path
EXCEL_PATH = f"data_{datetime.now().strftime('%d-%m-%Y_%H:%M:%S')}.xlsx"

progress = {"page": 0, "total": 0}

def ocr_pdf(pdf_path, lang="eng"):
    #output_txt="output.txt"
    global progress
    images = convert_from_path(pdf_path)
    records = []
    progress["total"] = len(images)

    for i, image in enumerate(images):
        progress["page"] = i + 1
        print(f"Processing page {i+1}/{len(images)}...")
        text = pytesseract.image_to_string(image, lang=lang)
        # Common data
        patient = re.search(r"PACIENTE:\s*(.*?)\s*(?=AFILIACION:)", text)
        affiliation = re.search(r"AFILIACION:\s*[-—]?\s*([\w\d]+ - [\w\d]+)", text)
      
        transfer = re.search(r"OFICIO DE TRASLADO:\s*[-—\s]*([0-9]+)", text)

        date = re.search(
            r"(?i)\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b\s+(\d{1,2}\s+DE\s+\w+\s+DE\s+\d{4})",
            text
        )
        ticket = re.search(r"(?i)(adultos?|niños?):\s*\$([\d,]+\.\d{2})", text)

        # All routes (there may be 2 or more)
        routes = re.findall(r"RUTA: DE:\s*(.+?)\s*(?=VIAJE:)", text)

        
        for r in routes:
            record = {
                "Patient": patient.group(1).strip() if patient else "",
                "Affiliation": affiliation.group(1).strip() if affiliation else "",
                "Transfer Document": transfer.group(1).strip() if transfer else "",
                "Date": date.group(2).strip() if date else "",
                "Route": r.strip(),
                "Ticket": ticket.group(2).strip() if ticket else ""
            }
            records.append(record)
        

        # Guardar todo el texto en un archivo
    #with open(output_txt, "w", encoding="utf-8") as f:
    #    f.write(text)
        

    df = pd.DataFrame(records)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return output

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["GET"])
def convert():
    excel_data = ocr_pdf(PDF_PATH)
    return send_file(
        excel_data,
        as_attachment=True,
        download_name=f"data_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/progress")
def get_progress():
    return jsonify(progress)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
