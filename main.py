class Paciente:
    def __init__(self, id_paciente, nome, idade):
        self.id_paciente = id_paciente
        self.nome = nome
        self.idade = idade

    def __repr__(self):
        return f"Paciente(id={self.id_paciente}, nome='{self.nome}', idade={self.idade})"


class TabelaHashPacientes:
    def __init__(self, tamanho=10):
        self.tamanho = tamanho
        self.tabela = [[] for _ in range(tamanho)]

    def _funcao_hash(self, id_paciente):
        return id_paciente % self.tamanho

    def inserir(self, paciente):
        indice = self._funcao_hash(paciente.id_paciente)
        for p in self.tabela[indice]:
            if p.id_paciente == paciente.id_paciente:
                p.nome = paciente.nome
                p.idade = paciente.idade
                return
        self.tabela[indice].append(paciente)

    def buscar(self, id_paciente):
        indice = self._funcao_hash(id_paciente)
        for p in self.tabela[indice]:
            if p.id_paciente == id_paciente:
                return p
        return None

    def remover(self, id_paciente):
        indice = self._funcao_hash(id_paciente)
        for i, p in enumerate(self.tabela[indice]):
            if p.id_paciente == id_paciente:
                del self.tabela[indice][i]
                return True
        return False


# Uso
th = TabelaHashPacientes(tamanho=7)
th.inserir(Paciente(101, "Ana Silva", 34))
th.inserir(Paciente(108, "Carlos Souza", 52))  # Colide no índice 3 com 101
print(th.buscar(108))