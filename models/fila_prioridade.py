from heapq import heappop, heappush

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
        self._proxima_versao = 0
        self._versoes = {}
        self._heap = []

    def _indice(self, chave):
        return hash(chave) % self.capacidade

    def adicionar(self, paciente):
        if not isinstance(paciente, Paciente):
            raise TypeError("O objeto deve ser um Paciente.")

        existente = self._buscar_no(paciente.id)
        if existente is not None:
            existente.paciente = paciente
            self._registrar_prioridade(paciente, existente.ordem_chegada)
            return False

        indice = self._indice(paciente.id)
        ordem = self._proxima_ordem_chegada
        self._proxima_ordem_chegada += 1
        novo = NoFila(paciente, ordem)
        novo.proximo = self.buckets[indice]
        self.buckets[indice] = novo
        self.tamanho += 1
        self._registrar_prioridade(paciente, ordem)

        if self.tamanho / self.capacidade >= self.fator_carga:
            self._redimensionar(self.capacidade * 2)
        return True

    def inserir(self, paciente):
        return self.adicionar(paciente)

    def buscar(self, id_paciente):
        no = self._buscar_no(id_paciente)
        return no.paciente if no is not None else None

    def _buscar_no(self, id_paciente):
        atual = self.buckets[self._indice(id_paciente)]
        while atual is not None:
            if atual.paciente.id == id_paciente:
                return atual
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
                self._versoes.pop(id_paciente, None)
                return atual.paciente
            anterior = atual
            atual = atual.proximo
        return None

    def _chave_prioridade(self, paciente, ordem_chegada):
        classificacao = CLASSIFICACAO_RISCO.get(
            paciente.classificacao, max(CLASSIFICACAO_RISCO.values()) + 1
        )
        return (classificacao, ordem_chegada)

    def _registrar_prioridade(self, paciente, ordem_chegada):
        versao = self._proxima_versao
        self._proxima_versao += 1
        self._versoes[paciente.id] = versao
        prioridade, ordem = self._chave_prioridade(paciente, ordem_chegada)
        heappush(self._heap, (prioridade, ordem, versao, paciente.id))

    def proximo(self):
        while self._heap:
            _, _, versao, id_paciente = self._heap[0]
            no = self._buscar_no(id_paciente)
            if no is not None and self._versoes.get(id_paciente) == versao:
                return no.paciente
            heappop(self._heap)
        return None

    def atender_proximo(self):
        paciente = self.proximo()
        return self.remover(paciente.id) if paciente is not None else None

    def reclassificar(self, id_paciente, classificacao):
        no = self._buscar_no(id_paciente)
        if no is None:
            return False
        no.paciente.classificacao = classificacao.upper()
        self._registrar_prioridade(no.paciente, no.ordem_chegada)
        return True

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