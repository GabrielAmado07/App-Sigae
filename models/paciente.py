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
        if not isinstance(horario, str):
            return datetime.min

        texto = horario.strip()
        for parser in (datetime.fromisoformat, time.fromisoformat):
            try:
                valor = parser(texto)
            except ValueError:
                continue
            return (
                valor
                if isinstance(valor, datetime)
                else datetime.combine(datetime.min.date(), valor)
            )
        return datetime.min