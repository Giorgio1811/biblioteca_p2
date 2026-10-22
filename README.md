# Sistema de Biblioteca — Projeto 2

Projeto de Construção de Backend (IESB) feito com Django. Gerencia autores, livros, membros, empréstimos e reservas, com regras de estoque, devolução, atraso e fila de atendimento.

## Funcionalidades

- Cadastro e administração de autores, livros, membros, empréstimos e reservas no Django Admin.
- Empréstimos com prazo de 14 dias, validação de estoque e limite de três empréstimos ativos por membro.
- Devolução idempotente: reabastece o estoque uma única vez.
- Detecção de atraso, cálculo de dias e multa de R$ 2,00 por dia.
- Fila FIFO de reserva quando não há cópias disponíveis.
- Relatório de livros mais emprestados com `annotate()` e `Count()`.
- Lembrete de e-mail dois dias antes do vencimento (comando agendável; console por padrão).
- Dashboard com gráfico de empréstimos por mês usando Chart.js.
- Testes automatizados para fluxos e regras de negócio.

## Requisitos

- Python 3.10 ou superior.
- Dependências instaladas a partir de `requirements.txt`.

## Como executar no Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py carregar_dados_demo
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/` e o painel administrativo em `http://127.0.0.1:8000/admin/`. O projeto usa SQLite local por padrão. Consulte `DOCUMENTACAO.txt` para o fluxo detalhado, decisões, desafios opcionais e configuração de e-mail.

## Verificação

```powershell
python manage.py check
python manage.py test
```

## Publicação

O arquivo `.gitignore` exclui ambientes virtuais, banco local, arquivos `.env` e caches. Antes de publicar, configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false` e `DJANGO_ALLOWED_HOSTS` no ambiente de produção. Nunca versionar senhas nem arquivos `.env`.

## Autor

Estudante — IESB, 2026
