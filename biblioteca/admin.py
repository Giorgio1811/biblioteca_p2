from django.contrib import admin

from .models import Autor, Emprestimo, Livro, Membro, Reserva


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ("nome", "nacionalidade", "data_nascimento")
    search_fields = ("nome",)


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "copias_totais", "copias_disponiveis")
    list_filter = ("autor",)
    search_fields = ("titulo", "isbn")


class EmprestimoInline(admin.TabularInline):
    model = Emprestimo
    extra = 0
    fields = (
        "livro",
        "data_emprestimo",
        "data_prevista_devolucao",
        "data_devolucao",
        "status",
        "lembrete_enviado_em",
    )
    readonly_fields = ("data_emprestimo", "lembrete_enviado_em")


class ReservaInline(admin.TabularInline):
    model = Reserva
    extra = 0
    fields = ("livro", "data_reserva", "status")
    readonly_fields = ("data_reserva",)


@admin.register(Membro)
class MembroAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "data_cadastro")
    search_fields = ("nome", "email")
    inlines = [EmprestimoInline, ReservaInline]


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = (
        "livro",
        "membro",
        "data_emprestimo",
        "data_prevista_devolucao",
        "status",
        "dias_atraso",
        "multa",
    )
    list_filter = ("status", "data_emprestimo")
    search_fields = ("livro__titulo", "membro__nome", "membro__email")
    readonly_fields = ("data_emprestimo", "lembrete_enviado_em")


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("livro", "membro", "data_reserva", "status")
    list_filter = ("status", "data_reserva")
    search_fields = ("livro__titulo", "membro__nome", "membro__email")
    readonly_fields = ("data_reserva",)
