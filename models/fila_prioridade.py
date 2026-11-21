from models.paciente import CLASSIFICACAO_RISCO, Paciente


class NoFila:
    def __init__(self, paciente):
        self.paciente = paciente
        self.proximo = None


class FilaHashEncadeada:
    """Tabela hash dinâmica que resolve colisões por encadeamento."""

    def __init__(self, capacidade_inicial=8, fator_carga=0.75,
                 criterio="CLASSIFICACAO"):
        if capacidade_inicial < 1:
            raise ValueError("A capacidade inicial deve ser maior que zero.")
        self.capacidade = capacidade_inicial
        self.fator_carga = fator_carga
        self.criterio = criterio
        self.buckets = [None] * capacidade_inicial
        self.tamanho = 0

    def _validar_criterio(self, criterio):
        if criterio not in ("CLASSIFICACAO", "CHEGADA"):
            raise ValueError("Critério deve ser CLASSIFICACAO ou CHEGADA.")

    def definir_criterio(self, criterio):
        criterio = criterio.upper()
        self._validar_criterio(criterio)
        self.criterio = criterio

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

        novo = NoFila(paciente)
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

    def _chave_prioridade(self, paciente):
        classificacao = CLASSIFICACAO_RISCO.get(
            paciente.classificacao, len(CLASSIFICACAO_RISCO) + 1
        )
        if self.criterio == "CHEGADA":
            return (paciente.horario, classificacao)
        return (classificacao, paciente.horario)

    def proximo(self):
        melhor = None

        for inicio in self.buckets:
            atual = inicio
            while atual is not None:
                paciente = atual.paciente
                if melhor is None or self._chave_prioridade(paciente) < self._chave_prioridade(melhor):
                    melhor = paciente
                atual = atual.proximo
        return melhor

    def atender_proximo(self):
        paciente = self.proximo()
        return self.remover(paciente.id) if paciente is not None else None

    def listar(self):
        pacientes = []
        for inicio in self.buckets:
            atual = inicio
            while atual is not None:
                pacientes.append(atual.paciente)
                atual = atual.proximo
        return sorted(pacientes, key=self._chave_prioridade)

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