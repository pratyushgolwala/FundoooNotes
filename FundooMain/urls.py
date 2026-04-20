"""
URL configuration for FundooMain project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

# User auth views
from users.views import login_view, signup_view, home
from users.api_views import SignupAPI, LoginAPI, HomeAPI

# Note views  
from notes.views import notes_list, note_create, note_update, note_delete
from notes.api_views import NotesAPI, NoteDetailAPI

# Label views
from labels.views import labels_list, label_create, label_update, label_delete

# Logout as utility
from django.views.generic import TemplateView
from django.contrib.auth import logout as auth_logout

# Swagger
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf import settings


def logout_view(request):
    """Simple logout view"""
    user_id = request.session.get('user_id')
    if request.method == "POST":
        request.session.flush()
        from django.shortcuts import redirect
        return redirect('login')
    from django.shortcuts import render
    user = None
    if user_id:
        try:
            from users.models import User
            user = User.objects.get(id=user_id)
        except:
            pass
    return render(request, "logout_confirm.html", {'user': user})


urlpatterns = [
    path('admin/', admin.site.urls),
    # User authentication
    path('', login_view, name='login'),
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),
    path('home/<int:user_id>/', home, name='home'),
    # Notes
    path("users/<int:user_id>/notes/", notes_list, name="notes-list"),
    path("users/<int:user_id>/notes/new/", note_create, name="note-create"),
    path("users/<int:user_id>/notes/<int:note_id>/edit/", note_update, name="note-update"),
    path("users/<int:user_id>/notes/<int:note_id>/delete/", note_delete, name="note-delete"),
    # Labels
    path("users/<int:user_id>/labels/", labels_list, name="labels-list"),
    path("users/<int:user_id>/labels/new/", label_create, name="label-create"),
    path("users/<int:user_id>/labels/<int:label_id>/edit/", label_update, name="label-update"),
    path("users/<int:user_id>/labels/<int:label_id>/delete/", label_delete, name="label-delete"),
]

# API endpoints
urlpatterns += [
    path("api/signup/", SignupAPI.as_view(), name="api-signup"),
    path("api/login/", LoginAPI.as_view(), name="api-login"),
    path("api/home/", HomeAPI.as_view(), name="api-home"),
    path("api/notes/", NotesAPI.as_view(), name="api-notes"),
    path("api/notes/<int:note_id>/", NoteDetailAPI.as_view(), name="api-note-detail"),
]

# Swagger UI
if settings.DEBUG:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]

