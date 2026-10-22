from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.core.management import call_command
from django.db.models import Count
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Autor, Emprestimo, Livro, Membro, Reserva


class RegrasDeNegocioTest(TestCase):
    def setUp(self):
        self.autor = Autor.objects.create(nome="Machado de Assis", nacionalidade="Brasileira")
        self.livro = Livro.objects.create(
            titulo="Dom Casmurro",
            autor=self.autor,
            isbn="111",
            copias_totais=1,
            copias_disponiveis=1,
        )
        self.sem_copia = Livro.objects.create(
            titulo="O Cortiço",
            autor=self.autor,
            isbn="222",
            copias_totais=1,
            copias_disponiveis=0,
        )
        self.membro = Membro.objects.create(nome="Ana", email="ana@iesb.br")

    def criar_emprestimo(self, livro=None, membro=None, **kwargs):
        kwargs.setdefault("data_prevista_devolucao", timezone.localdate())
        return Emprestimo.objects.create(
            livro=livro or self.livro,
            membro=membro or self.membro,
            **kwargs,
        )

    def test_emprestar_define_prazo_e_decrementa(self):
        resposta = self.client.post(
            reverse("emprestar_livro", args=[self.livro.pk]),
            {"membro_id": self.membro.pk},
        )
        self.assertEqual(resposta.status_code, 302)
        emprestimo = Emprestimo.objects.get()
        self.assertEqual(
            emprestimo.data_prevista_devolucao,
            timezone.localdate() + timedelta(days=14),
        )
        self.assertEqual(emprestimo.status, "ATIVO")
        self.livro.refresh_from_db()
        self.assertEqual(self.livro.copias_disponiveis, 0)

    def test_bloqueia_sem_copias(self):
        self.client.post(
            reverse("emprestar_livro", args=[self.sem_copia.pk]),
            {"membro_id": self.membro.pk},
        )
        self.assertEqual(Emprestimo.objects.count(), 0)
        self.sem_copia.refresh_from_db()
        self.assertEqual(self.sem_copia.copias_disponiveis, 0)

    def test_get_nao_empresta(self):
        resposta = self.client.get(reverse("emprestar_livro", args=[self.livro.pk]))
        self.assertEqual(resposta.status_code, 405)

    def test_devolver_repoe_estoque_e_nao_duplica(self):
        self.client.post(
            reverse("emprestar_livro", args=[self.livro.pk]),
            {"membro_id": self.membro.pk},
        )
        emprestimo = Emprestimo.objects.get()
        url = reverse("devolver_livro", args=[emprestimo.pk])
        self.client.post(url)
        self.client.post(url)
        emprestimo.refresh_from_db()
        self.livro.refresh_from_db()
        self.assertEqual(emprestimo.status, "DEVOLVIDO")
        self.assertEqual(emprestimo.data_devolucao, timezone.localdate())
        self.assertEqual(self.livro.copias_disponiveis, 1)

    def test_esta_atrasado_considera_status_e_prazo(self):
        hoje = timezone.localdate()
        atrasado = self.criar_emprestimo(data_prevista_devolucao=hoje - timedelta(days=1))
        no_prazo = self.criar_emprestimo(
            data_prevista_devolucao=hoje + timedelta(days=3),
        )
        devolvido = self.criar_emprestimo(
            data_prevista_devolucao=hoje - timedelta(days=5),
            status="DEVOLVIDO",
            data_devolucao=hoje,
        )
        self.assertTrue(atrasado.esta_atrasado)
        self.assertFalse(no_prazo.esta_atrasado)
        self.assertFalse(devolvido.esta_atrasado)

    def test_meus_emprestimos_mostra_badge_de_atraso(self):
        self.criar_emprestimo(data_prevista_devolucao=timezone.localdate() - timedelta(days=2))
        resposta = self.client.get(reverse("meus_emprestimos", args=[self.membro.pk]))
        self.assertContains(resposta, "Atrasado")

    def test_related_name_ranking_e_telas(self):
        self.assertEqual(self.autor.livros.count(), 2)
        for _ in range(3):
            self.criar_emprestimo()
        self.criar_emprestimo(livro=self.sem_copia)
        ranking = list(Livro.objects.annotate(total=Count("emprestimo")).order_by("-total"))
        self.assertEqual(ranking[0].titulo, "Dom Casmurro")
        self.assertEqual(ranking[0].total, 3)
        self.assertEqual(self.client.get(reverse("relatorio_livros")).status_code, 200)
        self.assertEqual(self.client.get(reverse("lista_livros")).status_code, 200)

    def test_admin_registrado(self):
        from django.contrib import admin

        for modelo in (Autor, Livro, Membro, Emprestimo, Reserva):
            self.assertIn(modelo, admin.site._registry)

    def test_admin_disponibiliza_tema_glassmorphism(self):
        from django.contrib.auth import get_user_model

        usuario = get_user_model().objects.create_superuser(
            username="admin_teste",
            email="admin@iesb.br",
            password="senha-segura-de-teste",
        )
        self.client.force_login(usuario)

        resposta = self.client.get(reverse("admin:index"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "biblioteca/css/admin_glass.css")
        self.assertContains(resposta, "biblioteca/js/admin_theme.js")
        self.assertContains(resposta, "biblioteca-admin-theme")

    def test_multa_calcula_dias_ate_devolucao_ou_hoje(self):
        hoje = timezone.localdate()
        emprestimo_aberto = self.criar_emprestimo(
            data_prevista_devolucao=hoje - timedelta(days=3),
        )
        emprestimo_devolvido = self.criar_emprestimo(
            data_prevista_devolucao=hoje - timedelta(days=5),
            data_devolucao=hoje - timedelta(days=2),
            status="DEVOLVIDO",
        )
        self.assertEqual(emprestimo_aberto.dias_atraso, 3)
        self.assertEqual(emprestimo_aberto.multa, Decimal("6.00"))
        self.assertEqual(emprestimo_devolvido.dias_atraso, 3)
        self.assertEqual(emprestimo_devolvido.multa, Decimal("6.00"))

    def test_limite_de_tres_emprestimos_ativos(self):
        for _ in range(3):
            self.criar_emprestimo()
        resposta = self.client.post(
            reverse("emprestar_livro", args=[self.livro.pk]),
            {"membro_id": self.membro.pk},
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Emprestimo.objects.count(), 3)
        self.livro.refresh_from_db()
        self.assertEqual(self.livro.copias_disponiveis, 1)

    def test_reserva_fila_fifo_e_prioridade(self):
        segundo_membro = Membro.objects.create(nome="Bia", email="bia@iesb.br")
        self.client.post(
            reverse("reservar_livro", args=[self.sem_copia.pk]),
            {"membro_id": self.membro.pk},
        )
        self.client.post(
            reverse("reservar_livro", args=[self.sem_copia.pk]),
            {"membro_id": segundo_membro.pk},
        )
        self.sem_copia.copias_disponiveis = 1
        self.sem_copia.save(update_fields=("copias_disponiveis",))

        self.client.post(
            reverse("emprestar_livro", args=[self.sem_copia.pk]),
            {"membro_id": segundo_membro.pk},
        )
        self.assertEqual(Emprestimo.objects.filter(livro=self.sem_copia).count(), 0)
        self.client.post(
            reverse("emprestar_livro", args=[self.sem_copia.pk]),
            {"membro_id": self.membro.pk},
        )
        self.assertEqual(Emprestimo.objects.filter(livro=self.sem_copia).count(), 1)
        self.assertEqual(
            Reserva.objects.get(livro=self.sem_copia, membro=self.membro).status,
            "ATENDIDA",
        )
        self.assertEqual(
            Reserva.objects.get(livro=self.sem_copia, membro=segundo_membro).status,
            "AGUARDANDO",
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_lembrete_email_enviado_uma_unica_vez(self):
        self.criar_emprestimo(
            data_prevista_devolucao=timezone.localdate() + timedelta(days=2),
        )
        call_command("enviar_lembretes", stdout=None)
        call_command("enviar_lembretes", stdout=None)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.membro.email])
        emprestimo = Emprestimo.objects.get()
        self.assertIsNotNone(emprestimo.lembrete_enviado_em)

    def test_dashboard_apresenta_indicadores_e_dados_graficos(self):
        self.criar_emprestimo()
        resposta = self.client.get(reverse("dashboard"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Dashboard da biblioteca")
        self.assertContains(resposta, "dados-mensais")
        self.assertContains(resposta, "Chart.js")

    def test_dados_demo_criam_minimos_e_sao_reexecutaveis(self):
        call_command("carregar_dados_demo", stdout=None)
        call_command("carregar_dados_demo", stdout=None)
        self.assertGreaterEqual(Autor.objects.count(), 3)
        self.assertGreaterEqual(Livro.objects.count(), 5)
        self.assertGreaterEqual(Membro.objects.count(), 3)
