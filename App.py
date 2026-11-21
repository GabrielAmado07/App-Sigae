from flask import Flask, redirect, render_template, request, url_for

from models.fila_prioridade import FilaHashEncadeada
from models.paciente import Paciente


app = Flask(__name__)
fila = FilaHashEncadeada()
proximo_id = 1


@app.route("/", methods=["GET", "POST"])
def index():
    global proximo_id

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        horario = request.form.get("horario", "").strip()
        classificacao = request.form.get("classificacao", "").upper()

        if nome and horario and classificacao:
            paciente = Paciente(nome, horario, proximo_id, classificacao)
            fila.adicionar(paciente)
            proximo_id += 1

        return redirect(url_for("index"))

    return render_template(
        "index.html",
        pacientes=fila.listar(),
        capacidade=fila.capacidade,
    )


@app.route("/atender", methods=["POST"])
def atender():
    fila.atender_proximo()
    return redirect(url_for("index"))


@app.route("/remover/<int:id_paciente>", methods=["POST"])
def remover(id_paciente):
    fila.remover(id_paciente)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
