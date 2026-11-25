import unittest
from datetime import date, timedelta

import App
from models.fila_prioridade import FilaHashEncadeada


class DoctorSchedulingTests(unittest.TestCase):
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

    def register_patient(self, name, urgency):
        response = self.client.post(
            "/cadastro",
            data={
                "nome": name,
                "horario": "10:00",
                "classificacao": urgency,
            },
        )
        self.assertEqual(response.status_code, 302)

    def call_next(self):
        return self.client.post("/atender")

    def finish_for(self, doctor):
        return self.client.post(
            "/finalizar",
            data={"medico_id": str(doctor["id"])},
        )

    def test_auto_id_daily_balance_and_tie_breakers(self):
        first = self.register_doctor("Doctor One", "URGENTE")
        second = self.register_doctor("Doctor Two", "URGENTE")
        self.assertEqual((first["id"], second["id"]), (1, 2))
        self.assertEqual(first["atendimentos_concluidos"], 0)
        self.assertEqual(second["atendimentos_concluidos"], 0)
        response = self.client.get("/medicos")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Urgente", response.data)

        patient = App.Paciente("Priority Patient", "10:00", 99, "URGENTE")
        today = date.today().isoformat()
        ontem = (date.today() - timedelta(days=1)).isoformat()
        first["atendimentos_por_dia"][ontem] = 10
        second["atendimentos_por_dia"][today] = 1
        self.assertIs(App.selecionar_medico(patient), first)
        first["atendimentos_por_dia"].clear()
        second["atendimentos_por_dia"].clear()

        first["ordem_cadastro"] = 2
        second["ordem_cadastro"] = 1
        self.assertIs(App.selecionar_medico(patient), second)
        first["ordem_cadastro"] = second["ordem_cadastro"]
        self.assertIs(App.selecionar_medico(patient), first)
        first["ordem_cadastro"] = first["id"]
        second["ordem_cadastro"] = second["id"]

        for index in range(4):
            self.register_patient(f"Urgent Patient {index}", "URGENTE")

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Doctor One", response.data)
        response = self.call_next()
        self.assertEqual(response.status_code, 302)
        self.assertIs(App.atendimentos_atuais[-1]["medico"], first)
        response = self.call_next()
        self.assertEqual(response.status_code, 302)
        self.assertIs(App.atendimentos_atuais[-1]["medico"], second)

        self.assertEqual(self.call_next().status_code, 409)
        self.assertEqual(App.fila.tamanho, 2)

        self.assertEqual(self.finish_for(first).status_code, 302)
        self.assertEqual(self.finish_for(second).status_code, 302)
        self.assertEqual(first["atendimentos_por_dia"][today], 1)
        self.assertEqual(second["atendimentos_por_dia"][today], 1)

        self.assertEqual(self.call_next().status_code, 302)
        self.assertIs(App.atendimentos_atuais[-1]["medico"], first)
        self.assertEqual(self.finish_for(first).status_code, 302)

        self.assertEqual(self.call_next().status_code, 302)
        self.assertIs(App.atendimentos_atuais[-1]["medico"], second)
        self.assertEqual(self.finish_for(second).status_code, 302)
        self.assertEqual(first["atendimentos_concluidos"], 2)
        self.assertEqual(second["atendimentos_concluidos"], 2)
        self.assertEqual(self.client.get("/medicos").status_code, 200)

    def test_only_matching_urgency_doctors_are_selected(self):
        urgent_doctor = self.register_doctor("Urgent Doctor", "URGENTE")
        emergency_doctor = self.register_doctor("Emergency Doctor", "EMERGENCIA")
        self.register_patient("Urgent Patient", "URGENTE")
        self.register_patient("Emergency Patient", "EMERGENCIA")

        response = self.call_next()
        self.assertEqual(response.status_code, 302)
        self.assertIs(App.atendimentos_atuais[-1]["medico"], emergency_doctor)
        self.assertEqual(self.finish_for(emergency_doctor).status_code, 302)

        response = self.call_next()
        self.assertEqual(response.status_code, 302)
        self.assertIs(App.atendimentos_atuais[-1]["medico"], urgent_doctor)

    def test_patient_stays_queued_without_matching_doctor(self):
        self.register_doctor("Urgent Doctor", "URGENTE")
        self.register_patient("Very Urgent Patient", "MUITO_URGENTE")

        self.assertEqual(self.call_next().status_code, 409)
        self.assertEqual(App.fila.tamanho, 1)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"n\xc3\xa3o h\xc3\xa1 m\xc3\xa9dicos cadastrados", response.data.lower())


if __name__ == "__main__":
    unittest.main()
