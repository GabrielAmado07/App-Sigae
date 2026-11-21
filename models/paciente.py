CLASSIFICACAO_RISCO = {
    "EMERGENCIA": 1,
    "MUITO_URGENTE": 2,
    "URGENTE": 3,
    "POUCO_URGENTE": 4,
    "NAO_URGENTE": 5,
}


class Paciente:
    def __init__(
        self,
        id_paciente: str,
        nome: str,
        horario_chegada: str,
        classificacao_risco: str,
    ) -> None:
        self.id_paciente = id_paciente
        self.nome = nome
        self.horario_chegada = horario_chegada
        self.classificacao_risco = classificacao_risco
        self.prioridade = CLASSIFICACAO_RISCO.get(classificacao_risco, 5)


class _NoEncadeado:
    def __init__(self, paciente: Paciente, proximo=None) -> None:
        self.paciente = paciente
        self.proximo = proximo


class FilaHashEncadeamento:
    def __init__(self, capacidade: int = 16) -> None:
        if capacidade <= 0:
            raise ValueError("A capacidade deve ser maior que zero.")
        self.capacidade = capacidade
        self.tamanho = 0
        self.contador_id = 0
        self.tabela = [None] * capacidade

    def _gerar_id(self) -> str:
        self.contador_id += 1
        return f"PAC-{self.contador_id:04d}"

    def _hash(self, chave: str) -> int:
        soma = 0
        for indice, caractere in enumerate(chave):
            soma += (indice + 1) * ord(caractere)
        return soma % self.capacidade

    def inserir(
        self,
        nome: str,
        horario_chegada: str,
        classificacao_risco: str,
    ) -> Paciente:
        id_gerado = self._gerar_id()
        paciente = Paciente(
            id_paciente=id_gerado,
            nome=nome.strip(),
            horario_chegada=horario_chegada.strip(),
            classificacao_risco=classificacao_risco.strip(),
        )
        indice = self._hash(paciente.id_paciente)

        novo_no = _NoEncadeado(paciente=paciente, proximo=self.tabela[indice])
        self.tabela[indice] = novo_no
        self.tamanho += 1
        return paciente

    def buscar(self, id_paciente: str):
        chave = id_paciente.strip().upper()
        indice = self._hash(chave)
        atual = self.tabela[indice]

        while atual is not None:
            if atual.paciente.id_paciente == chave:
                return atual.paciente
            atual = atual.proximo

        return None

    def remover(self, id_paciente: str):
        chave = id_paciente.strip().upper()
        indice = self._hash(chave)
        atual = self.tabela[indice]
        anterior = None

        while atual is not None:
            if atual.paciente.id_paciente == chave:
                if anterior is None:
                    self.tabela[indice] = atual.proximo
                else:
                    anterior.proximo = atual.proximo
                self.tamanho -= 1
                return atual.paciente

            anterior = atual
            atual = atual.proximo

        return None

    def listar_todos(self) -> list:
        pacientes = []
        for cabeca in self.tabela:
            atual = cabeca
            while atual is not None:
                pacientes.append(atual.paciente)
                atual = atual.proximo

        pacientes.sort(key=lambda p: (p.prioridade, p.horario_chegada))
        return pacientes