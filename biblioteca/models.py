from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Autor(models.Model):
    nome = models.CharField(max_length=150)
    nacionalidade = models.CharField(max_length=80)
    data_nascimento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.nome


class Livro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE, related_name="livros")
    isbn = models.CharField(max_length=20, unique=True)
    copias_totais = models.PositiveIntegerField()
    copias_disponiveis = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(copias_disponiveis__lte=F("copias_totais")),
                name="livro_disponiveis_ate_total",
            ),
        ]

    def __str__(self):
        return self.titulo


class Membro(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    data_cadastro = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Emprestimo(models.Model):
    STATUS_CHOICES = [
        ("ATIVO", "Ativo"),
        ("DEVOLVIDO", "Devolvido"),
        ("ATRASADO", "Atrasado"),
    ]

    livro = models.ForeignKey(Livro, on_delete=models.CASCADE)
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE)
    data_emprestimo = models.DateField(auto_now_add=True)
    data_prevista_devolucao = models.DateField()
    data_devolucao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ATIVO")
    lembrete_enviado_em = models.DateTimeField(null=True, blank=True)

    @property
    def esta_atrasado(self):
        return (
            self.status in ("ATIVO", "ATRASADO")
            and self.data_prevista_devolucao < timezone.localdate()
        )

    @property
    def dias_atraso(self):
        data_limite = self.data_devolucao or timezone.localdate()
        return max((data_limite - self.data_prevista_devolucao).days, 0)

    @property
    def multa(self):
        valor_diario = Decimal(str(settings.MULTA_DIARIA))
        return (valor_diario * self.dias_atraso).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.membro} -> {self.livro}"


class Reserva(models.Model):
    STATUS_CHOICES = [
        ("AGUARDANDO", "Aguardando"),
        ("ATENDIDA", "Atendida"),
        ("CANCELADA", "Cancelada"),
    ]

    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name="reservas")
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name="reservas")
    data_reserva = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="AGUARDANDO")

    class Meta:
        ordering = ("data_reserva", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("livro", "membro"),
                condition=Q(status="AGUARDANDO"),
                name="reserva_pendente_unica_por_membro",
            ),
        ]

    def __str__(self):
        return f"{self.membro} — {self.livro} ({self.get_status_display()})"
