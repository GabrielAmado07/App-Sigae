from datetime import datetime

from flask import Flask, abort, redirect, render_template, request, url_for

from models.fila_prioridade import FilaHashEncadeada
from models.paciente import CLASSIFICACAO_RISCO, Paciente


app = Flask(__name__)
fila = FilaHashEncadeada()
proximo_id = 1
pacientes_atendidos = []
atendimentos_atuais = []
medicos = []
proximo_id_medico = 1


def obter_medicos_disponiveis():
    ids_medicos_ocupados = {
        atendimento["medico"]["id"] for atendimento in atendimentos_atuais
    }
    return [
        medico for medico in medicos
        if medico["id"] not in ids_medicos_ocupados
    ]


@app.route("/")
def index():
    id_busca = request.args.get("id", "").strip()
    termo_remocao = request.args.get("remover", "").strip()
    paciente_encontrado = None
    mensagem_busca = None
    candidatos_remocao = []
    mensagem_remocao = None

    if id_busca:
        try:
            id_paciente = int(id_busca)
        except ValueError:
            mensagem_busca = "Digite um ID numérico válido."
        else:
            paciente_encontrado = fila.buscar(id_paciente)
            if paciente_encontrado is None:
                mensagem_busca = f"Nenhum paciente encontrado com o ID {id_paciente}."

    if termo_remocao:
        candidatos_remocao = []
        try:
            id_remocao = int(termo_remocao)
        except ValueError:
            termo_normalizado = termo_remocao.casefold()
            candidatos_remocao = [
                paciente for paciente in fila.listar()
                if termo_normalizado in paciente.nome.casefold()
            ]
        else:
            paciente = fila.buscar(id_remocao)
            candidatos_remocao = [paciente] if paciente is not None else []

        if not candidatos_remocao:
            mensagem_remocao = f"Nenhum paciente encontrado para remoção: {termo_remocao}."

    return render_template(
        "index.html",
        pacientes=fila.listar(),
        capacidade=fila.capacidade,
        pacientes_atendidos=pacientes_atendidos,
        atendimentos_atuais=atendimentos_atuais,
        medicos_disponiveis=obter_medicos_disponiveis(),
        id_busca=id_busca,
        paciente_encontrado=paciente_encontrado,
        mensagem_busca=mensagem_busca,
        termo_remocao=termo_remocao,
        candidatos_remocao=candidatos_remocao,
        mensagem_remocao=mensagem_remocao,
    )


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    global proximo_id

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        horario = request.form.get("horario", "").strip()
        classificacao = request.form.get("classificacao", "").strip().upper()

        if not nome or not horario:
            abort(400, description="Nome e horário são obrigatórios.")

        if classificacao not in CLASSIFICACAO_RISCO:
            abort(400, description="Classificação de risco inválida.")

        paciente = Paciente(nome, horario, proximo_id, classificacao)
        fila.adicionar(paciente)
        proximo_id += 1

        return redirect(url_for("index"))

    return render_template("cadastro.html")


@app.route("/medicos", methods=["GET", "POST"])
def cadastro_medicos():
    global proximo_id_medico

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()

        if not nome:
            abort(400, description="O nome do médico é obrigatório.")

        medicos.append({
            "id": proximo_id_medico,
            "nome": nome,
            "atendimentos_concluidos": 0,
        })
        proximo_id_medico += 1
        return redirect(url_for("cadastro_medicos"))

    return render_template("medicos.html", medicos=medicos)


@app.route("/atender", methods=["POST"])
def atender():
    if not medicos:
        abort(409, description="Cadastre um médico antes de chamar um paciente.")

    medicos_livres = obter_medicos_disponiveis()
    if not medicos_livres:
        abort(409, description="Todos os médicos estão em atendimento.")

    medico = medicos_livres[0]

    paciente = fila.atender_proximo()
    if paciente is not None:
        paciente.status = "EM_ATENDIMENTO"
        atendimentos_atuais.append({
            "paciente": paciente,
            "medico": medico,
            "chamado_em": datetime.now(),
        })
    return redirect(url_for("index"))


@app.route("/finalizar", methods=["POST"])
def finalizar_atendimento():
    try:
        id_medico = int(request.form.get("medico_id", ""))
    except ValueError:
        abort(400, description="Não foi possível identificar o médico.")

    atendimento = next(
        (
            item for item in atendimentos_atuais
            if item["medico"]["id"] == id_medico
        ),
        None,
    )
    if atendimento is None:
        abort(404, description="Não há paciente em atendimento.")

    paciente = atendimento["paciente"]
    medico = atendimento["medico"]
    paciente.status = "ATENDIDO"
    medico["atendimentos_concluidos"] += 1
    pacientes_atendidos.append({
        "paciente": paciente,
        "medico": medico,
        "atendido_em": datetime.now(),
    })
    atendimentos_atuais.remove(atendimento)
    return redirect(url_for("index"))


@app.route("/reclassificar/<int:id_paciente>", methods=["POST"])
def reclassificar(id_paciente):
    paciente = fila.buscar(id_paciente)
    if paciente is None:
        abort(404, description="Paciente não encontrado na fila.")

    classificacao = request.form.get("classificacao", "").strip().upper()
    if classificacao not in CLASSIFICACAO_RISCO:
        abort(400, description="Classificação de risco inválida.")

    paciente.classificacao = classificacao
    return redirect(url_for("index"))


@app.route("/remover/<int:id_paciente>", methods=["POST"])
def remover(id_paciente):
    paciente = fila.remover(id_paciente)
    if paciente is not None:
        paciente.status = "REMOVIDO"
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
