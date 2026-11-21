CLASSIFICACAO_RISCO = {
    "EMERGENCIA": 1,
    "MUITO_URGENTE": 2,
    "URGENTE": 3,
    "POUCO_URGENTE": 4,
    "NAO_URGENTE": 5,
}

class Paciente:
    def __init__(self, nome,horario,id,classificação):
        self.nome = nome
        self.horario = horario
        self.id = id
        self.classificação = classificação