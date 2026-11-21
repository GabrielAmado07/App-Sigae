from flask import Flask, redirect, render_template, request, url_for
from fila_prioridade import FilaPrioridadeHashEncadeada
from paciente import Paciente

app = Flask(__name__)
fila = FilaPrioridadeHashEncadeada(capacidade_inicial=8, fator_carga_maximo=0.75)
proximo_id = 1


@app.route("/", methods=["GET", "POST"])
def index():
    global proximo_id

    if request.method == "POST":
        nome = request.form["nome"]
        horario = request.form["horario"]
        classificacao = request.form["classificacao"]

        paciente = Paciente(
            nome=nome,
            horario=horario,
            id=proximo_id,
            classificação=classificacao,
        )
        proximo_id += 1
        fila.inserir(paciente)
        return redirect(url_for("index"))

    return render_template(
        "index.html",
        pacientes=fila.listar_ordenados(),
        total_pacientes=fila.quantidade,
        capacidade_hash=fila.capacidade,
    )