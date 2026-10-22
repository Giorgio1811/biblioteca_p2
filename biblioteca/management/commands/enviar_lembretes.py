from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from biblioteca.models import Emprestimo


class Command(BaseCommand):
    help = "Envia lembretes para empréstimos ativos que vencem em dois dias."

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        data_limite = hoje + timedelta(days=2)
        emprestimos = (
            Emprestimo.objects.filter(
                status="ATIVO",
                data_devolucao__isnull=True,
                data_prevista_devolucao=data_limite,
                lembrete_enviado_em__isnull=True,
            )
            .select_related("livro", "membro")
            .order_by("pk")
        )

        enviados = 0
        for emprestimo in emprestimos:
            quantidade = send_mail(
                subject=f"Lembrete de devolução: {emprestimo.livro.titulo}",
                message=(
                    f"Olá, {emprestimo.membro.nome}.\n\n"
                    f"O prazo para devolver '{emprestimo.livro.titulo}' é "
                    f"{emprestimo.data_prevista_devolucao:%d/%m/%Y} "
                    "(daqui a dois dias).\n"
                    "A Biblioteca agradece."
                ),
                from_email=None,
                recipient_list=[emprestimo.membro.email],
                fail_silently=False,
            )
            if quantidade != 1:
                raise CommandError(
                    f"O backend não confirmou o envio do lembrete "
                    f"do empréstimo {emprestimo.pk}."
                )
            emprestimo.lembrete_enviado_em = timezone.now()
            emprestimo.save(update_fields=("lembrete_enviado_em",))
            enviados += 1

        self.stdout.write(self.style.SUCCESS(f"Lembretes enviados: {enviados}."))
