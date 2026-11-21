from paciente import CLASSIFICACAO_RISCO, Paciente

class NoEncadeado:
    def __init__(self, paciente: Paciente, proximo: "NoEncadeado | None" = None):
        self.paciente = paciente
        self.proximo = proximo


class FilaPrioridadeHashEncadeada:
    def __init__(
        self,
        capacidade_inicial: int = 8,
        fator_carga_maximo: float = 0.75,
        arvore_rubro_negra=None,
    ):
        self.capacidade = capacidade_inicial
        self.fator_carga_maximo = fator_carga_maximo
        self.quantidade = 0
        self.tabela: list[NoEncadeado | None] = [None] * self.capacidade
        # Referência futura para a Árvore Rubro-Negra (pode ser plugada depois)
        self.arvore_rubro_negra = arvore_rubro_negra

    def vincular_arvore(self, arvore_rubro_negra) -> None:
        """Permite acoplar a Árvore Rubro-Negra após instanciar a fila."""
        self.arvore_rubro_negra = arvore_rubro_negra

    def _hash(self, chave, capacidade: int | None = None) -> int:
        cap = capacidade if capacidade is not None else self.capacidade
        if isinstance(chave, int):
            return chave % cap
        soma = sum(ord(caractere) for caractere in str(chave))
        return soma % cap

    @property
    def fator_carga(self) -> float:
        return self.quantidade / self.capacidade

    def _redimensionar(self, nova_capacidade: int) -> None:
        """Aumenta a tabela hash e reinsere os nós encadeados (rehashing)."""
        tabela_antiga = self.tabela
        self.capacidade = nova_capacidade
        self.tabela = [None] * nova_capacidade

        for cabeca in tabela_antiga:
            atual = cabeca
            while atual is not None:
                proximo_no = atual.proximo
                indice = self._hash(atual.paciente.id, nova_capacidade)
                # Insere no início do novo bucket
                atual.proximo = self.tabela[indice]
                self.tabela[indice] = atual
                atual = proximo_no

    def _notificar_insercao_arvore(self, paciente: Paciente) -> None:
        if self.arvore_rubro_negra is not None and hasattr(
            self.arvore_rubro_negra, "inserir"
        ):
            self.arvore_rubro_negra.inserir(paciente)

    def _notificar_remocao_arvore(self, paciente: Paciente) -> None:
        if self.arvore_rubro_negra is not None and hasattr(
            self.arvore_rubro_negra, "remover"
        ):
            self.arvore_rubro_negra.remover(paciente)

    def inserir(self, paciente: Paciente) -> int:
        """Insere o paciente, cresce a tabela se necessário e notifica a árvore."""
        if self.buscar_por_id(paciente.id) is not None:
            raise ValueError(f"Já existe um paciente com ID {paciente.id}.")

        # Cresce antes de inserir se ultrapassar o fator de carga
        if (self.quantidade + 1) / self.capacidade > self.fator_carga_maximo:
            self._redimensionar(self.capacidade * 2)

        indice = self._hash(paciente.id)
        novo_no = NoEncadeado(paciente=paciente, proximo=self.tabela[indice])
        self.tabela[indice] = novo_no
        self.quantidade += 1

        self._notificar_insercao_arvore(paciente)
        return indice

    def buscar_por_id(self, paciente_id) -> Paciente | None:
        indice = self._hash(paciente_id)
        atual = self.tabela[indice]
        while atual is not None:
            if atual.paciente.id == paciente_id:
                return atual.paciente
            atual = atual.proximo
        return None

    def remover_por_id(self, paciente_id) -> Paciente | None:
        indice = self._hash(paciente_id)
        atual = self.tabela[indice]
        anterior: NoEncadeado | None = None

        while atual is not None:
            if atual.paciente.id == paciente_id:
                if anterior is None:
                    self.tabela[indice] = atual.proximo
                else:
                    anterior.proximo = atual.proximo
                self.quantidade -= 1
                removido = atual.paciente
                self._notificar_remocao_arvore(removido)
                return removido
            anterior = atual
            atual = atual.proximo

        return None

    def _chave_prioridade(self, paciente: Paciente):
        peso_risco = CLASSIFICACAO_RISCO.get(paciente.classificação, 99)
        return (peso_risco, paciente.horario)

    def listar_todos(self) -> list[Paciente]:
        """Percorre todos os buckets e nós encadeados."""
        pacientes: list[Paciente] = []
        for cabeca in self.tabela:
            atual = cabeca
            while atual is not None:
                pacientes.append(atual.paciente)
                atual = atual.proximo
        return pacientes

    def listar_ordenados(self) -> list[Paciente]:
        """
        Quando a Árvore Rubro-Negra estiver pronta, você pode delegar
        a ordenação/consulta de prioridade a ela se desejar.
        """
        return sorted(self.listar_todos(), key=self._chave_prioridade)

    def atender_proximo(self) -> Paciente | None:
        ordenados = self.listar_ordenados()
        if not ordenados:
            return None
        proximo = ordenados[0]
        return self.remover_por_id(proximo.id)