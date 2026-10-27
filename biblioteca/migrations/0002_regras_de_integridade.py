from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("biblioteca", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="livro",
            constraint=models.CheckConstraint(
                condition=Q(copias_totais__gt=0)
                & Q(copias_disponiveis__gte=0),
                name="livro_estoque_valido",
            ),
        ),
        migrations.AddConstraint(
            model_name="emprestimo",
            constraint=models.CheckConstraint(
                condition=(
                    Q(status="DEVOLVIDO", data_devolucao__isnull=False)
                    | Q(
                        status__in=("ATIVO", "ATRASADO"),
                        data_devolucao__isnull=True,
                    )
                ),
                name="emprestimo_status_compativel_data",
            ),
        ),
    ]
