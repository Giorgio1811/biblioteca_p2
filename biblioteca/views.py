from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, F, Prefetch
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Emprestimo, Livro, Membro, Reserva

LIMITE_EMPRESTIMOS_ATIVOS = 3


def lista_livros(request):
    livros = (
        Livro.objects.select_related("autor")
        .prefetch_related(
            Prefetch(
                "reservas",
                queryset=Reserva.objects.filter(status="AGUARDANDO").select_related("membro"),
                to_attr="reservas_pendentes",
            )
        )
        .order_by("titulo")
    )
    membros = Membro.objects.order_by("nome")
    return render(
        request,
        "biblioteca/lista_livros.html",
        {"livros": livros, "membros": membros},
    )


def _membro_do_post(request):
    membro_id = request.POST.get("membro_id", "")
    if not membro_id.isdecimal():
        return None
    return Membro.objects.filter(pk=int(membro_id)).first()


@require_POST
def emprestar_livro(request, livro_id):
    membro = _membro_do_post(request)
    if membro is None:
        messages.error(request, "Selecione um membro válido para registrar o empréstimo.")
        return redirect("lista_livros")

    hoje = timezone.localdate()
    with transaction.atomic():
        livro = get_object_or_404(Livro.objects.select_for_update(), pk=livro_id)
        reservas = Reserva.objects.select_for_update().filter(
            livro=livro,
            status="AGUARDANDO",
        ).order_by("data_reserva", "pk")
        primeira_reserva = reservas.first()
        if primeira_reserva and primeira_reserva.membro_id != membro.pk:
            messages.error(
                request,
                f'Este livro está reservado. A próxima reserva é de {primeira_reserva.membro.nome}.',
            )
            return redirect("lista_livros")

        emprestimos_ativos = Emprestimo.objects.filter(
            membro=membro,
            status__in=("ATIVO", "ATRASADO"),
            data_devolucao__isnull=True,
        ).count()
        if emprestimos_ativos >= LIMITE_EMPRESTIMOS_ATIVOS:
            messages.error(request, "Cada membro pode manter no máximo 3 empréstimos ativos.")
            return redirect("lista_livros")

        estoque_atualizado = Livro.objects.filter(
            pk=livro.pk,
            copias_disponiveis__gt=0,
        ).update(copias_disponiveis=F("copias_disponiveis") - 1)
        if not estoque_atualizado:
            messages.error(request, f'Não há cópias disponíveis de "{livro.titulo}" no momento.')
            return redirect("lista_livros")

        Emprestimo.objects.create(
            livro=livro,
            membro=membro,
            data_prevista_devolucao=hoje + timedelta(days=14),
        )
        if primeira_reserva:
            primeira_reserva.status = "ATENDIDA"
            primeira_reserva.save(update_fields=("status",))

    messages.success(request, f'Empréstimo de "{livro.titulo}" registrado com sucesso!')
    return redirect("lista_livros")


@require_POST
def reservar_livro(request, livro_id):
    membro = _membro_do_post(request)
    if membro is None:
        messages.error(request, "Selecione um membro válido para reservar o livro.")
        return redirect("lista_livros")

    with transaction.atomic():
        livro = get_object_or_404(Livro.objects.select_for_update(), pk=livro_id)
        if livro.copias_disponiveis > 0:
            messages.warning(request, "Há cópias disponíveis; faça o empréstimo diretamente.")
            return redirect("lista_livros")
        if Reserva.objects.filter(livro=livro, membro=membro, status="AGUARDANDO").exists():
            messages.warning(request, "Este membro já está na fila de reserva deste livro.")
            return redirect("lista_livros")
        Reserva.objects.create(livro=livro, membro=membro)

    messages.success(request, f'Reserva de "{livro.titulo}" registrada no fim da fila.')
    return redirect("lista_livros")


@require_POST
def devolver_livro(request, emprestimo_id):
    hoje = timezone.localdate()
    with transaction.atomic():
        emprestimo = get_object_or_404(
            Emprestimo.objects.select_related("livro", "membro").select_for_update(),
            pk=emprestimo_id,
        )
        atualizado = Emprestimo.objects.filter(
            pk=emprestimo.pk,
            status__in=("ATIVO", "ATRASADO"),
            data_devolucao__isnull=True,
        ).update(status="DEVOLVIDO", data_devolucao=hoje)
        if not atualizado:
            messages.warning(request, "Este empréstimo já foi devolvido.")
            return redirect("meus_emprestimos", membro_id=emprestimo.membro_id)

        estoque_atualizado = Livro.objects.filter(
            pk=emprestimo.livro_id,
            copias_disponiveis__lt=F("copias_totais"),
        ).update(copias_disponiveis=F("copias_disponiveis") + 1)
        if not estoque_atualizado:
            raise ValueError(
                f"Estoque inconsistente para o livro {emprestimo.livro_id}: "
                "não é possível registrar a devolução."
            )

    messages.success(request, f'Devolução de "{emprestimo.livro.titulo}" registrada.')
    return redirect("meus_emprestimos", membro_id=emprestimo.membro_id)


def meus_emprestimos(request, membro_id):
    membro = get_object_or_404(Membro, pk=membro_id)
    emprestimos = membro.emprestimo_set.select_related("livro").order_by("-data_emprestimo")
    return render(
        request,
        "biblioteca/meus_emprestimos.html",
        {"membro": membro, "emprestimos": emprestimos},
    )


def relatorio_livros(request):
    livros = (
        Livro.objects.select_related("autor")
        .annotate(total_emprestimos=Count("emprestimo"))
        .order_by("-total_emprestimos", "titulo")
    )
    return render(request, "biblioteca/relatorio_livros.html", {"livros": livros})


def dashboard(request):
    totais_mensais = (
        Emprestimo.objects.annotate(mes=TruncMonth("data_emprestimo"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )
    dados_mensais = [
        {"mes": item["mes"].strftime("%Y-%m"), "total": item["total"]}
        for item in totais_mensais
    ]
    return render(
        request,
        "biblioteca/dashboard.html",
        {
            "total_livros": Livro.objects.count(),
            "total_membros": Membro.objects.count(),
            "emprestimos_ativos": Emprestimo.objects.filter(
                status__in=("ATIVO", "ATRASADO"),
                data_devolucao__isnull=True,
            ).count(),
            "dados_mensais": dados_mensais,
        },
    )
