from datetime import datetime, time


CLASSIFICACAO_RISCO = {
    "EMERGENCIA": 1,
    "MUITO_URGENTE": 2,
    "URGENTE": 3,
    "POUCO_URGENTE": 4,
    "NAO_URGENTE": 5,
}


class Paciente:
    def __init__(self, nome, horario, id, classificacao):
        self.nome = nome
        self.horario = self._normalizar_horario(horario)
        self.id = id
        self.classificacao = classificacao.upper()
        self.status = "AGUARDANDO"

    @staticmethod
    def _normalizar_horario(horario):
        if isinstance(horario, datetime):
            return horario
        if isinstance(horario, str):
            texto = horario.strip()
            if texto:
                try:
                    return datetime.fromisoformat(texto)
                except ValueError:
                    try:
                        return datetime.combine(datetime.min.date(), time.fromisoformat(texto))
                    except ValueError:
                        return datetime.min
        return datetime.min