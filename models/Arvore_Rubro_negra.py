
RED, BLACK = 0, 1


class No:
    def __init__(self, chave, valor=None):
        self.chave = chave
        self.valor = chave if valor is None else valor
        self.cor = RED
        self.esq = None
        self.dir = None
        self.pai = None


class ArvoreRubroNegra:
    """Arvore rubro-negra com chaves comparaveis, como tuplas (horario, id)."""

    def __init__(self):
        self.NIL = No(None)
        self.NIL.cor = BLACK
        self.NIL.pai = self.NIL
        self.raiz = self.NIL
        self.tamanho = 0

    def inserir(self, chave, valor=None):
        existente = self._buscar_no(chave)
        if existente is not None:
            existente.valor = chave if valor is None else valor
            self.validar()
            return False

        novo = No(chave, valor)
        novo.esq = novo.dir = self.NIL

        pai = self.NIL
        atual = self.raiz
        while atual != self.NIL:
            pai = atual
            atual = atual.esq if chave < atual.chave else atual.dir

        novo.pai = pai
        if pai == self.NIL:
            self.raiz = novo
        elif chave < pai.chave:
            pai.esq = novo
        else:
            pai.dir = novo

        self.tamanho += 1
        self._corrigir_insercao(novo)
        self.validar()
        return True

    def _corrigir_insercao(self, z):
        while z.pai.cor == RED:
            avo = z.pai.pai
            if z.pai == avo.esq:
                tio = avo.dir
                if tio.cor == RED:
                    z.pai.cor = BLACK
                    tio.cor = BLACK
                    avo.cor = RED
                    z = avo
                else:
                    if z == z.pai.dir:
                        z = z.pai
                        self._rot_esq(z)
                    z.pai.cor = BLACK
                    avo.cor = RED
                    self._rot_dir(avo)
            else:
                tio = avo.esq
                if tio.cor == RED:
                    z.pai.cor = BLACK
                    tio.cor = BLACK
                    avo.cor = RED
                    z = avo
                else:
                    if z == z.pai.esq:
                        z = z.pai
                        self._rot_dir(z)
                    z.pai.cor = BLACK
                    avo.cor = RED
                    self._rot_esq(avo)
        self.raiz.cor = BLACK

    def _rot_esq(self, x):
        y = x.dir
        x.dir = y.esq
        if y.esq != self.NIL:
            y.esq.pai = x
        y.pai = x.pai
        if x.pai == self.NIL:
            self.raiz = y
        elif x == x.pai.esq:
            x.pai.esq = y
        else:
            x.pai.dir = y
        y.esq = x
        x.pai = y

    def _rot_dir(self, x):
        y = x.esq
        x.esq = y.dir
        if y.dir != self.NIL:
            y.dir.pai = x
        y.pai = x.pai
        if x.pai == self.NIL:
            self.raiz = y
        elif x == x.pai.dir:
            x.pai.dir = y
        else:
            x.pai.esq = y
        y.dir = x
        x.pai = y

    def buscar(self, chave):
        no = self._buscar_no(chave)
        return None if no is None else no.valor

    def _buscar_no(self, chave):
        atual = self.raiz
        while atual != self.NIL:
            if chave == atual.chave:
                return atual
            atual = atual.esq if chave < atual.chave else atual.dir
        return None

    def remover(self, chave):
        z = self._buscar_no(chave)
        if z is None:
            self.validar()
            return None

        valor_removido = z.valor
        y = z
        cor_original = y.cor
        if z.esq == self.NIL:
            x = z.dir
            self._transplantar(z, z.dir)
        elif z.dir == self.NIL:
            x = z.esq
            self._transplantar(z, z.esq)
        else:
            y = self._minimo(z.dir)
            cor_original = y.cor
            x = y.dir
            if y.pai == z:
                x.pai = y
            else:
                self._transplantar(y, y.dir)
                y.dir = z.dir
                y.dir.pai = y
            self._transplantar(z, y)
            y.esq = z.esq
            y.esq.pai = y
            y.cor = z.cor

        if cor_original == BLACK:
            self._corrigir_remocao(x)

        self.tamanho -= 1
        self.validar()
        return valor_removido

    def _transplantar(self, u, v):
        if u.pai == self.NIL:
            self.raiz = v
        elif u == u.pai.esq:
            u.pai.esq = v
        else:
            u.pai.dir = v
        v.pai = u.pai

    def _minimo(self, no):
        while no.esq != self.NIL:
            no = no.esq
        return no

    def _corrigir_remocao(self, x):
        while x != self.raiz and x.cor == BLACK:
            if x == x.pai.esq:
                w = x.pai.dir
                if w.cor == RED:
                    w.cor = BLACK
                    x.pai.cor = RED
                    self._rot_esq(x.pai)
                    w = x.pai.dir
                if w.esq.cor == BLACK and w.dir.cor == BLACK:
                    w.cor = RED
                    x = x.pai
                else:
                    if w.dir.cor == BLACK:
                        w.esq.cor = BLACK
                        w.cor = RED
                        self._rot_dir(w)
                        w = x.pai.dir
                    w.cor = x.pai.cor
                    x.pai.cor = BLACK
                    w.dir.cor = BLACK
                    self._rot_esq(x.pai)
                    x = self.raiz
            else:
                w = x.pai.esq
                if w.cor == RED:
                    w.cor = BLACK
                    x.pai.cor = RED
                    self._rot_dir(x.pai)
                    w = x.pai.esq
                if w.dir.cor == BLACK and w.esq.cor == BLACK:
                    w.cor = RED
                    x = x.pai
                else:
                    if w.esq.cor == BLACK:
                        w.dir.cor = BLACK
                        w.cor = RED
                        self._rot_esq(w)
                        w = x.pai.esq
                    w.cor = x.pai.cor
                    x.pai.cor = BLACK
                    w.esq.cor = BLACK
                    self._rot_dir(x.pai)
                    x = self.raiz
        x.cor = BLACK

    def percurso_em_ordem(self):
        resultado = []

        def visitar(no):
            if no == self.NIL:
                return
            visitar(no.esq)
            resultado.append(no.valor)
            visitar(no.dir)

        visitar(self.raiz)
        return resultado

    def listar_chaves(self):
        resultado = []

        def visitar(no):
            if no == self.NIL:
                return
            visitar(no.esq)
            resultado.append(no.chave)
            visitar(no.dir)

        visitar(self.raiz)
        return resultado

    def validar(self):
        if self.raiz == self.NIL:
            return True
        if self.raiz.cor != BLACK:
            raise AssertionError("A raiz da arvore deve ser preta.")

        chaves = self.listar_chaves()
        if chaves != sorted(chaves):
            raise AssertionError("O percurso em ordem deve estar ordenado.")

        def verificar(no):
            if no == self.NIL:
                return 1
            if no.cor == RED:
                if no.esq.cor == RED or no.dir.cor == RED:
                    raise AssertionError("Nao pode haver dois nós vermelhos consecutivos.")
            if no.pai == self.NIL:
                if no != self.raiz:
                    raise AssertionError("Pai invalido.")
            elif no.pai.esq != no and no.pai.dir != no:
                raise AssertionError("Ligacao pai-filho invalida.")

            altura_esq = verificar(no.esq)
            altura_dir = verificar(no.dir)
            if altura_esq != altura_dir:
                raise AssertionError("Caminhos devem ter a mesma quantidade de nós pretos.")
            return altura_esq + (1 if no.cor == BLACK else 0)

        verificar(self.raiz)
        if len(chaves) != self.tamanho:
            raise AssertionError("O tamanho informado diverge dos nós da arvore.")
        return True