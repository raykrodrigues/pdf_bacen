from flask import Flask, request, render_template, send_file
import pdfplumber
import re
import os
import zipfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def limpar_valor(valor):
    return valor.replace("+", "").replace("=", "").strip()


def processar_pdf(caminho_pdf):
    texto = ""

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto += "\n" + t

    tarifas = re.findall(r"TARIFA\s+(\d{1,3}(?:\.\d{3})*,\d{2})", texto)
    taxas = re.findall(r"TAXA\s+(\d{1,3}(?:\.\d{3})*,\d{2})", texto)
    totais = re.findall(r"TOTAL\s+(\d{1,3}(?:\.\d{3})*,\d{2})", texto)
    paxs = re.findall(r"Pax:\s*(.*?)\s*/", texto, re.IGNORECASE)

    linhas = []
    for i in range(len(totais)):
        tarifa = tarifas[i] if i < len(tarifas) else "0,00"
        taxa = taxas[i] if i < len(taxas) else "0,00"
        total = totais[i]
        passageiro = paxs[i] if i < len(paxs) else "SEM_PAX"

        linha = (
            f"2026/{str(i+1).zfill(6)}-01-01;"
            f"{limpar_valor(tarifa)},{limpar_valor(taxa)};"
            f"0,00;0,00;{limpar_valor(total)};"
            f"LATAM AIRLINES BRASIL;{passageiro}"
        )

        linhas.append(linha)

    return linhas


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        arquivos = request.files.getlist("files")

        arquivos_gerados = []
        zip_path = os.path.join(UPLOAD_FOLDER, "resultado.zip")

        with zipfile.ZipFile(zip_path, "w") as zipf:

            for arquivo in arquivos:
                nome = secure_filename(arquivo.filename)
                caminho_pdf = os.path.join(UPLOAD_FOLDER, nome)
                arquivo.save(caminho_pdf)

                linhas = processar_pdf(caminho_pdf)

                txt_nome = nome.replace(".pdf", ".txt")
                caminho_txt = os.path.join(UPLOAD_FOLDER, txt_nome)

                with open(caminho_txt, "w", encoding="utf-8") as f:
                    f.write("Requisicoes;Tarifa,Taxa;Embarque;Multa;Total;Cia Aérea;Passageiro\n")
                    f.write("\n".join(linhas))

                zipf.write(caminho_txt, txt_nome)
                arquivos_gerados.append(txt_nome)

        return render_template("index.html", arquivos=arquivos_gerados, zip_ready=True)

    return render_template("index.html", arquivos=None, zip_ready=False)


@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)


@app.route("/download-zip")
def download_zip():
    return send_file(os.path.join(UPLOAD_FOLDER, "resultado.zip"), as_attachment=True)


if __name__ == "__main__":
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000)

    