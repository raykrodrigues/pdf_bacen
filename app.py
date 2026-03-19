from flask import Flask, request, render_template, send_file
import pdfplumber
import re
import os
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
    cia = "LATAM AIRLINES BRASIL"

    for i in range(len(totais)):
        tarifa = tarifas[i] if i < len(tarifas) else "0,00"
        taxa = taxas[i] if i < len(taxas) else "0,00"
        total = totais[i]
        passageiro = paxs[i] if i < len(paxs) else "SEM_PAX"

        req = f"2026/{str(i+1).zfill(6)}-01-01"

        linha = (
            f"{req};{limpar_valor(tarifa)},{limpar_valor(taxa)};"
            f"0,00;0,00;{limpar_valor(total)};"
            f"{cia};{passageiro}"
        )

        linhas.append(linha)

    return linhas


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        arquivos = request.files.getlist("files")

        arquivos_gerados = []

        for arquivo in arquivos:
            nome_seguro = secure_filename(arquivo.filename)
            caminho_pdf = os.path.join(UPLOAD_FOLDER, nome_seguro)
            arquivo.save(caminho_pdf)

            linhas = processar_pdf(caminho_pdf)

            txt_nome = nome_seguro.replace(".pdf", ".txt")
            caminho_txt = os.path.join(UPLOAD_FOLDER, txt_nome)

            with open(caminho_txt, "w", encoding="utf-8") as f:
                f.write("Requisicoes;Tarifa,Taxa;Embarque;Multa;Total;Cia Aérea;Passageiro\n")
                f.write("\n".join(linhas))

            arquivos_gerados.append(txt_nome)

        return render_template("index.html", arquivos=arquivos_gerados)

    return render_template("index.html", arquivos=None)


@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)