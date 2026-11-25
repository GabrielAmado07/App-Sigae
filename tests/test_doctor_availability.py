import unittest
from datetime import datetime

import App
from models.fila_prioridade import FilaHashEncadeada
from models.Arvore_Rubro_negra import ArvoreRubroNegra
from models.paciente import Paciente


class DoctorAvailabilityTests(unittest.TestCase):
    def setUp(self):
        App.fila = FilaHashEncadeada()
        App.proximo_id = 1
        App.pacientes_atendidos.clear()
        App.atendimentos_atuais.clear()
        App.medicos.clear()
        App.proximo_id_medico = 1
        self.client = App.app.test_client()

    def register_doctor(self, name, urgency):
        response = self.client.post(
            "/medicos",
            data={"nome": name, "urgencia": urgency},
        )
        self.assertEqual(response.status_code, 302)
        return App.medicos[-1]

    def test_availability_toggle_and_lists(self):
        doctor = self.register_doctor("Doctor Alpha", "URGENTE")
        self.register_doctor("Doctor Beta", "EMERGENCIA")

        page = self.client.get("/medicos")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Doctor Alpha", page.data)
        self.assertIn(b"name=\"disponivel\"", page.data)

        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Doctor Alpha", page.data)
        self.assertIn(b"M\xc3\xa9dicos dispon\xc3\xadveis na triagem", page.data)

        response = self.client.post(
            "/medicos/1/disponibilidade",
            data={"disponivel": "0"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(doctor["disponivel"])
        self.assertNotIn(doctor, App.obter_medicos_disponiveis())

        self.client.post(
            "/cadastro",
            data={
                "nome": "Urgent Patient",
                "horario": "10:00",
                "classificacao": "URGENTE",
            },
        )
        response = self.client.post("/atender")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(App.fila.tamanho, 1)

        response = self.client.post(
            "/medicos/1/disponibilidade",
            data={"disponivel": "1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(doctor["disponivel"])
        page = self.client.get("/")
        self.assertIn(b"Doctor Alpha", page.data)
        self.assertIn(b"M\xc3\xa9dico selecionado: Doctor Alpha", page.data)
        self.assertIn(
            b"m\xc3\xa9dicos dispon\xc3\xadveis para esta urg\xc3\xaancia",
            page.data.lower(),
        )

    def test_search_and_removal_by_name_or_id(self):
        doctor = self.register_doctor("Doctor Alpha", "URGENTE")
        self.register_doctor("Doctor Beta", "EMERGENCIA")

        self.assertIn(b"Doctor Alpha", self.client.get(
            "/medicos?buscar_medico=Alpha"
        ).data)
        page = self.client.get("/medicos?buscar_medico=2")
        self.assertIn(b"Doctor Beta", page.data)
        self.assertNotIn(b"Doctor Alpha", page.data)

        response = self.client.post(
            "/medicos/1/remover",
            data={"buscar_medico": "Alpha"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(doctor, App.medicos)
        self.assertNotIn(b"Doctor Alpha", self.client.get(
            "/medicos?buscar_medico=Alpha"
        ).data)

        response = self.client.post("/medicos/2/remover")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(App.medicos, [])

    def test_cannot_remove_doctor_with_active_patient(self):
        doctor = self.register_doctor("Doctor Alpha", "URGENTE")
        self.client.post(
            "/cadastro",
            data={
                "nome": "Urgent Patient",
                "horario": "10:00",
                "classificacao": "URGENTE",
            },
        )
        self.assertEqual(self.client.post("/atender").status_code, 302)
        response = self.client.post("/medicos/1/remover")
        self.assertEqual(response.status_code, 409)
        self.assertIn(doctor, App.medicos)
        self.assertEqual(
            self.client.post("/finalizar", data={"medico_id": "1"}).status_code,
            302,
        )


class RedBlackTreeTests(unittest.TestCase):
    def test_insert_search_remove_and_validate(self):
        arvore = ArvoreRubroNegra()
        chaves = [(datetime(2026, 1, 1, 10, minuto), minuto) for minuto in range(1, 13)]

        for chave in reversed(chaves):
            arvore.inserir(chave)

        self.assertTrue(arvore.validar())
        self.assertEqual(arvore.percurso_em_ordem(), chaves)
        self.assertEqual(arvore.buscar(chaves[5]), chaves[5])

        for chave in chaves:
            self.assertEqual(arvore.remover(chave), chave)
            self.assertTrue(arvore.validar())

        self.assertEqual(arvore.tamanho, 0)
        self.assertEqual(arvore.remover(chaves[0]), None)

    def test_queue_keeps_chronological_rb_index(self):
        fila = FilaHashEncadeada()
        pacientes = [
            Paciente("Terceiro", "12:00", 3, "URGENTE"),
            Paciente("Primeiro", "10:00", 1, "NAO_URGENTE"),
            Paciente("Segundo", "11:00", 2, "EMERGENCIA"),
        ]

        for paciente in pacientes:
            fila.adicionar(paciente)

        self.assertEqual(
            [paciente.id for paciente in fila.listar_cronologico()],
            [1, 2, 3],
        )
        self.assertTrue(fila.arvore_chegada.validar())

        fila.remover(2)
        self.assertEqual(
            [paciente.id for paciente in fila.listar_cronologico()],
            [1, 3],
        )
        self.assertTrue(fila.arvore_chegada.validar())


if __name__ == "__main__":
    unittest.main()
