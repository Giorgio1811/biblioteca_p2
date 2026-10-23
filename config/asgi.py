import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_asgi_application()

if os.environ.get("VERCEL") == "1":
    from django.core.management import call_command

    call_command("migrate", interactive=False, verbosity=0)
    call_command("carregar_dados_demo", verbosity=0)
