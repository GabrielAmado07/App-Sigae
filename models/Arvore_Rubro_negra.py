
RED, BLACK = 0, 1


class No:
    def __init__(self, chave):
        self.chave = chave
        self.cor = RED
        self.esq = self.dir = None
        self.pai = None


class ArvoreRubroNegra:
    def __init__(self):
        self.NIL = No(None)
        self.NIL.cor = BLACK
        self.raiz = self.NIL

    def inserir(self, chave):
        novo = No(chave)
        novo.esq = novo.dir = self.NIL

        pai, atual = None, self.raiz

        while atual != self.NIL:
            pai = atual
            atual = atual.esq if chave < atual.chave else atual.dir

        novo.pai = pai

        if pai == None:
            self.raiz = novo
        elif chave < pai.chave:
            pai.esq = novo
        else:
            pai.dir = novo

        self._corrigir_insercao(novo)

    def _corrigir_insercao(self, z):
        while z.pai and z.pai.cor == RED:
            avo = z.pai.pai

            if z.pai == avo.esq:
                tio = avo.dir

                if tio.cor == RED:
                    z.pai.cor = tio.cor = BLACK
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
                    z.pai.cor = tio.cor = BLACK
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

        if x.pai == None:
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

        if x.pai == None:
            self.raiz = y
        elif x == x.pai.dir:
            x.pai.dir = y
        else:
            x.pai.esq = y

        y.dir = x
        x.pai = y


arvore = ArvoreRubroNegra()

valores = [10, 20, 30]

for valor in valores:
    arvore.inserir(valor)


    def mostrar_arvore(no, NIL, nivel=0):
        if no == NIL:
            return

        mostrar_arvore(no.dir, NIL, nivel + 1)

        cor = "Vermelho" if no.cor == RED else "Preto"

        print("    " * nivel, no.chave, cor)

        mostrar_arvore(no.esq, NIL, nivel + 1)


mostrar_arvore(arvore.raiz, arvore.NIL)