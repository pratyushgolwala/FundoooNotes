"""
ASGI config for FundooMain project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django

from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Mount

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FundooMain.settings")

# Initialize Django first, before importing FastAPI
django.setup()

from FundooMain.fastapi import app as fastapi_app

django_asgi_app = get_asgi_application()

application = Starlette(
    routes=[
        Mount("/fastapi", app=fastapi_app),
        Mount("/", app=django_asgi_app),
    ]
)