from models.paciente import CLASSIFICACAO_RISCO, Paciente


class NoFila:
    def __init__(self, paciente, ordem_chegada):
        self.paciente = paciente
        self.ordem_chegada = ordem_chegada
        self.proximo = None


class FilaHashEncadeada:
    """Tabela hash dinâmica que resolve colisões por encadeamento."""

    def __init__(self, capacidade_inicial=8, fator_carga=0.75):
        if capacidade_inicial < 1:
            raise ValueError("A capacidade inicial deve ser maior que zero.")
        self.capacidade = capacidade_inicial
        self.fator_carga = fator_carga
        self.buckets = [None] * capacidade_inicial
        self.tamanho = 0
        self._proxima_ordem_chegada = 0

    def _indice(self, chave):
        return hash(chave) % self.capacidade

    def adicionar(self, paciente):
        if not isinstance(paciente, Paciente):
            raise TypeError("O objeto deve ser um Paciente.")

        indice = self._indice(paciente.id)
        atual = self.buckets[indice]
        while atual is not None:
            if atual.paciente.id == paciente.id:
                atual.paciente = paciente
                return False
            atual = atual.proximo

        novo = NoFila(paciente, self._proxima_ordem_chegada)
        self._proxima_ordem_chegada += 1
        novo.proximo = self.buckets[indice]
        self.buckets[indice] = novo
        self.tamanho += 1

        if self.tamanho / self.capacidade >= self.fator_carga:
            self._redimensionar(self.capacidade * 2)
        return True

    def inserir(self, paciente):
        return self.adicionar(paciente)

    def buscar(self, id_paciente):
        atual = self.buckets[self._indice(id_paciente)]
        while atual is not None:
            if atual.paciente.id == id_paciente:
                return atual.paciente
            atual = atual.proximo
        return None

    def remover(self, id_paciente):
        indice = self._indice(id_paciente)
        atual = self.buckets[indice]
        anterior = None

        while atual is not None:
            if atual.paciente.id == id_paciente:
                if anterior is None:
                    self.buckets[indice] = atual.proximo
                else:
                    anterior.proximo = atual.proximo
                self.tamanho -= 1
                return atual.paciente
            anterior = atual
            atual = atual.proximo
        return None

    def _chave_prioridade(self, paciente, ordem_chegada):
        classificacao = CLASSIFICACAO_RISCO.get(
            paciente.classificacao, len(CLASSIFICACAO_RISCO) + 1
        )
        return (classificacao, ordem_chegada)

    def proximo(self):
        melhor = None

        for inicio in self.buckets:
            atual = inicio
            while atual is not None:
                paciente = atual.paciente
                if melhor is None or self._chave_prioridade(
                    paciente, atual.ordem_chegada
                ) < self._chave_prioridade(
                    melhor.paciente, melhor.ordem_chegada
                ):
                    melhor = atual
                atual = atual.proximo
        return melhor.paciente if melhor is not None else None

    def atender_proximo(self):
        paciente = self.proximo()
        return self.remover(paciente.id) if paciente is not None else None

    def listar(self):
        pacientes = []
        for inicio in self.buckets:
            atual = inicio
            while atual is not None:
                pacientes.append((atual.paciente, atual.ordem_chegada))
                atual = atual.proximo
        pacientes.sort(
            key=lambda item: self._chave_prioridade(item[0], item[1])
        )
        return [paciente for paciente, _ in pacientes]

    def _redimensionar(self, nova_capacidade):
        buckets_antigos = self.buckets
        self.capacidade = nova_capacidade
        self.buckets = [None] * nova_capacidade

        for inicio in buckets_antigos:
            atual = inicio
            while atual is not None:
                seguinte = atual.proximo
                indice = self._indice(atual.paciente.id)
                atual.proximo = self.buckets[indice]
                self.buckets[indice] = atual
                atual = seguinte