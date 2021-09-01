"""register URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from britishdenim import views
from django.contrib import admin
from django.urls import path
from user import views as user_views
from django.contrib.auth import views as authentication_views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'britishdenim'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/<sku>', views.register, name='register' ),
    path('profile/', user_views.profile, name='profile'),
    path('signin/', user_views.signin, name='signin'),
    path('login/', user_views.LoginView.as_view(), name='login'),
    path('logout/', authentication_views.LogoutView.as_view(template_name='index.html'), name='logout'),
    path('', views.index, name='index'),
    path('contact/', views.contact, name='contact'),
    path('rewards/', views.rewards, name= 'rewards'),
]

urlpatterns += [
    # ... the rest of your URLconf goes here ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
