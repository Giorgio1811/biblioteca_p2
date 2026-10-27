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
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py carregar_dados_demo
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/` e o painel administrativo em `http://127.0.0.1:8000/admin/`. O projeto usa SQLite local por padrão. Consulte `DOCUMENTACAO.txt` para o fluxo detalhado, decisões, desafios opcionais e configuração de e-mail.

Para validar a instalação local antes de iniciar o servidor, execute `python manage.py check` e `python manage.py test`.

## Deploy na Vercel com Supabase

O projeto pode ser conectado ao repositório GitHub como uma aplicação Django em Python. A Vercel detecta `manage.py` e usa `config.asgi:application`; `STATIC_ROOT` está configurado para que os arquivos estáticos sejam coletados durante o build. O banco local continua sendo SQLite; em Vercel, a aplicação exige PostgreSQL e usa `DATABASE_URL` do Supabase.

1. Crie um projeto no [Supabase](https://supabase.com/dashboard) e defina uma senha forte para o banco.
2. No painel Supabase, abra **Connect** e copie a URI do **Transaction pooler** (porta `6543`). Não publique nem envie essa URI: ela contém a senha do banco.
3. No projeto Vercel, abra **Settings → Environment Variables** e adicione `DATABASE_URL` com essa URI para **Production** e **Preview**. Se preferir conexão direta, use a conexão IPv6 direta fornecida pelo Supabase.
4. Configure também estas variáveis de ambiente na Vercel:

- `DJANGO_SECRET_KEY`: uma chave secreta forte e exclusiva. Gere uma localmente com `python -c "import secrets; print(secrets.token_urlsafe(50))"` e cadastre o resultado diretamente nas configurações da Vercel.
- `DJANGO_DEBUG`: `false`.
- `DJANGO_ALLOWED_HOSTS`: `.vercel.app` e, se houver, o domínio personalizado, separados por vírgula.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: origens HTTPS do projeto e domínio personalizado, separadas por vírgula (por exemplo, `https://*.vercel.app,https://biblioteca.exemplo.com`).

As variáveis podem ser configuradas em **Production**, **Preview** e **Development** conforme necessário. Não é necessário configurar um comando de build personalizado. A Vercel instala as dependências de `requirements.txt` e coleta os arquivos estáticos. As migrações não são executadas automaticamente na inicialização da função. Após configurar `DATABASE_URL`, sincronize as variáveis localmente com `vercel env pull .env.local --environment=production`, execute `python manage.py migrate` e crie a conta administrativa com `python manage.py createsuperuser`. Para carregar os dados de demonstração, execute opcionalmente `python manage.py carregar_dados_demo`. Como `.env.local` é ignorado pelo Git, a URI do banco não será versionada.

Após adicionar todas as variáveis na Vercel, faça um novo deploy. A senha da conexão deve ser mantida somente nos painéis do Supabase/Vercel e no arquivo local ignorado `.env.local`; nunca a inclua no Git ou em mensagens.

## Verificação

```powershell
python manage.py check
python manage.py test
```

## Publicação

O arquivo `.gitignore` exclui ambientes virtuais, banco local, arquivos `.env` e caches. Antes de publicar, configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false` e `DJANGO_ALLOWED_HOSTS` no ambiente de produção. Nunca versionar senhas nem arquivos `.env`.

## Autor

Estudante — IESB, 2026
