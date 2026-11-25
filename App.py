from datetime import date, datetime
from threading import Lock

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
estado_lock = Lock()
NOMES_URGENCIA = {
    "EMERGENCIA": "Emergência",
    "MUITO_URGENTE": "Muito Urgente",
    "URGENTE": "Urgente",
    "POUCO_URGENTE": "Pouco Urgente",
    "NAO_URGENTE": "Não Urgente",
}


def obter_medicos_disponiveis(urgencia=None):
    ids_medicos_ocupados = {
        atendimento["medico"]["id"] for atendimento in atendimentos_atuais
    }
    return [
        medico for medico in medicos
        if medico["id"] not in ids_medicos_ocupados
        and (urgencia is None or medico["urgencia"] == urgencia)
    ]


def selecionar_medico(paciente, medicos_disponiveis=None):
    if paciente is None:
        return None

    candidatos = (
        obter_medicos_disponiveis(paciente.classificacao)
        if medicos_disponiveis is None
        else medicos_disponiveis
    )
    if not candidatos:
        return None

    hoje = date.today().isoformat()
    return min(
        candidatos,
        key=lambda medico: (
            medico["atendimentos_por_dia"].get(hoje, 0),
            medico["ordem_cadastro"],
            medico["id"],
        ),
    )


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

    proximo_paciente = fila.proximo()
    urgencia_proximo = (
        proximo_paciente.classificacao if proximo_paciente is not None else None
    )
    medicos_da_urgencia = [
        medico for medico in medicos
        if urgencia_proximo is not None and medico["urgencia"] == urgencia_proximo
    ]
    medicos_disponiveis = obter_medicos_disponiveis(urgencia_proximo)
    medico_selecionado = selecionar_medico(proximo_paciente, medicos_disponiveis)

    return render_template(
        "index.html",
        pacientes=fila.listar(),
        capacidade=fila.capacidade,
        pacientes_atendidos=pacientes_atendidos,
        atendimentos_atuais=atendimentos_atuais,
        proximo_paciente=proximo_paciente,
        medicos_da_urgencia=medicos_da_urgencia,
        medicos_disponiveis=medicos_disponiveis,
        medico_selecionado=medico_selecionado,
        nomes_urgencia=NOMES_URGENCIA,
        data_hoje=date.today().isoformat(),
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
        urgencia = request.form.get("urgencia", "").strip().upper()

        if not nome or urgencia not in CLASSIFICACAO_RISCO:
            abort(400, description="Informe o nome e um tipo de urgência válido.")

        with estado_lock:
            medicos.append({
                "id": proximo_id_medico,
                "nome": nome,
                "urgencia": urgencia,
                "ordem_cadastro": proximo_id_medico,
                "atendimentos_concluidos": 0,
                "atendimentos_por_dia": {},
            })
            proximo_id_medico += 1
        return redirect(url_for("cadastro_medicos"))

    return render_template(
        "medicos.html",
        medicos=medicos,
        data_hoje=date.today().isoformat(),
        nomes_urgencia=NOMES_URGENCIA,
    )


@app.route("/atender", methods=["POST"])
def atender():
    with estado_lock:
        paciente = fila.proximo()
        if paciente is None:
            return redirect(url_for("index"))

        medicos_da_urgencia = [
            medico for medico in medicos
            if medico["urgencia"] == paciente.classificacao
        ]
        if not medicos_da_urgencia:
            abort(
                409,
                description=(
                    "Não há médico cadastrado para a urgência "
                    f"{paciente.classificacao.replace('_', ' ').lower()}."
                ),
            )

        medico = selecionar_medico(paciente)
        if medico is None:
            abort(409, description="Todos os médicos desta urgência estão em atendimento.")

        if fila.remover(paciente.id) is None:
            abort(409, description="O paciente não está mais na fila.")

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

    with estado_lock:
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
        hoje = date.today().isoformat()
        medico["atendimentos_por_dia"][hoje] = (
            medico["atendimentos_por_dia"].get(hoje, 0) + 1
        )
        pacientes_atendidos.append({
            "paciente": paciente,
            "medico": medico,
            "atendido_em": datetime.now(),
        })
        atendimentos_atuais.remove(atendimento)
    return redirect(url_for("index"))


@app.route("/reclassificar/<int:id_paciente>", methods=["POST"])
def reclassificar(id_paciente):
    if fila.buscar(id_paciente) is None:
        abort(404, description="Paciente não encontrado na fila.")

    classificacao = request.form.get("classificacao", "").strip().upper()
    if classificacao not in CLASSIFICACAO_RISCO:
        abort(400, description="Classificação de risco inválida.")

    fila.reclassificar(id_paciente, classificacao)
    return redirect(url_for("index"))


@app.route("/remover/<int:id_paciente>", methods=["POST"])
def remover(id_paciente):
    paciente = fila.remover(id_paciente)
    if paciente is not None:
        paciente.status = "REMOVIDO"
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
