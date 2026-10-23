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

## Deploy de demonstração na Vercel

O projeto pode ser conectado ao repositório GitHub como uma aplicação Django em Python. A Vercel detecta `manage.py` e usa `config.asgi:application`; `STATIC_ROOT` está configurado para que os arquivos estáticos sejam coletados durante o build.

No projeto Vercel, configure as variáveis de ambiente para **Production** e **Preview**:

- `DJANGO_SECRET_KEY`: uma chave secreta forte e exclusiva. Gere uma localmente com `python -c "import secrets; print(secrets.token_urlsafe(50))"` e cadastre o resultado diretamente nas configurações da Vercel.
- `DJANGO_DEBUG`: `false`.
- `DJANGO_ALLOWED_HOSTS`: `.vercel.app` e, se houver, o domínio personalizado, separados por vírgula.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: origens HTTPS do projeto e domínio personalizado, separadas por vírgula (por exemplo, `https://*.vercel.app,https://biblioteca.exemplo.com`).

Não é necessário configurar um comando de build personalizado. A Vercel instala as dependências de `requirements.txt` e coleta os arquivos estáticos. Cada nova instância serverless cria e preenche seu próprio SQLite temporário em `/tmp`; alterações não são persistidas e podem não aparecer em outras instâncias ou após uma nova inicialização. Esta configuração serve apenas para demonstração. Para manter cadastros, empréstimos, sessões administrativas ou consistência entre usuários, conecte um PostgreSQL persistente antes de usar em produção.

## Verificação

```powershell
python manage.py check
python manage.py test
```

## Publicação

O arquivo `.gitignore` exclui ambientes virtuais, banco local, arquivos `.env` e caches. Antes de publicar, configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false` e `DJANGO_ALLOWED_HOSTS` no ambiente de produção. Nunca versionar senhas nem arquivos `.env`.

## Autor

Estudante — IESB, 2026
