from django.core.management.base import BaseCommand

from biblioteca.models import Autor, Livro, Membro


class Command(BaseCommand):
    help = "Cria autores, livros e membros fictícios para demonstração local."

    def handle(self, *args, **options):
        autores_dados = [
            ("Machado de Assis", "Brasileira"),
            ("Clarice Lispector", "Brasileira"),
            ("José de Alencar", "Brasileira"),
        ]
        autores = {
            nome: Autor.objects.get_or_create(
                nome=nome,
                defaults={"nacionalidade": nacionalidade},
            )[0]
            for nome, nacionalidade in autores_dados
        }

        livros_dados = [
            ("Dom Casmurro", "Machado de Assis", "9780000000001"),
            (
                "Memórias Póstumas de Brás Cubas",
                "Machado de Assis",
                "9780000000002",
            ),
            ("A Hora da Estrela", "Clarice Lispector", "9780000000003"),
            ("Laços de Família", "Clarice Lispector", "9780000000004"),
            ("O Guarani", "José de Alencar", "9780000000005"),
        ]
        for titulo, nome_autor, isbn in livros_dados:
            Livro.objects.get_or_create(
                isbn=isbn,
                defaults={
                    "titulo": titulo,
                    "autor": autores[nome_autor],
                    "copias_totais": 2,
                    "copias_disponiveis": 2,
                },
            )

        membros_dados = [
            ("Ana Silva", "ana.silva@example.com"),
            ("Bruno Souza", "bruno.souza@example.com"),
            ("Carla Lima", "carla.lima@example.com"),
        ]
        for nome, email in membros_dados:
            Membro.objects.get_or_create(email=email, defaults={"nome": nome})

        self.stdout.write(
            self.style.SUCCESS(
                "Dados de demonstração verificados: 3 autores, 5 livros "
                "e 3 membros."
            )
        )
