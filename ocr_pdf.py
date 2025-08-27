import os
import re
from pdf2image import convert_from_path
import pytesseract
import pandas as pd

def ocr_pdf(pdf_path, excel_file="datos.xlsx", lang="spa"):
    images = convert_from_path(pdf_path)
    registros = []

    for i, image in enumerate(images):
        print(f"Procesando página {i+1}...")
        texto = pytesseract.image_to_string(image, lang=lang)

        # Datos comunes
        paciente = re.search(r"PACIENTE:\s*(.*?)\s*(?=AFILIACION:)", texto)
        afiliacion = re.search(r"AFILIACION:\s*[-—]?\s*([\w\d]+ - [\w\d]+)", texto)
        #afiliacion = re.search(r"AFILIACION:\s*[—]?\s*(\S+)\s*-\s*(\S+)", texto)
        oficio = re.search(r"OFICIO DE TRASLADO:\s*[-—\s]*([0-9]+)", texto)

        fecha = re.search(
            r"(?i)\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b\s+(\d{1,2}\s+DE\s+\w+\s+DE\s+\d{4})",
            texto
        )
        pasaje = re.search(r"(?i)(adultos?|niños?):\s*\$([\d,]+\.\d{2})", texto)

        # Todas las rutas (puede haber 2 o más)
        rutas = re.findall(r"RUTA: DE:\s*(.+?)\s*(?=VIAJE:)", texto)
    
        # Crear un registro por cada ruta encontrada
        for r in rutas:
            registro = {
                "Paciente": paciente.group(1).strip() if paciente else "",
                "Afiliación": afiliacion.group(1).strip() if afiliacion else "",
                "Oficio de traslado": oficio.group(1).strip() if oficio else "",
                "Fecha": fecha.group(2).strip() if fecha else "",
                "Ruta": r.strip(),
                "Pasaje": pasaje.group(2).strip() if pasaje else ""
            }
            registros.append(registro)

    # Guardar en Excel
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
        df = pd.concat([df, pd.DataFrame(registros)], ignore_index=True)
    else:
        df = pd.DataFrame(registros)

    df.to_excel(excel_file, index=False)
    print(f"{len(registros)} filas agregadas a {excel_file}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python ocr_pdf.py archivo_escaneado.pdf")
        sys.exit(1)

    pdf_file = sys.argv[1]
    ocr_pdf(pdf_file)
