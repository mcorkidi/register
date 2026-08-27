
from britishdenim import views
from britishdenim.views import ProductViewSet, LoginAPIView, LogOutAPIView, LoggedInUser
from django.contrib import admin
from django.urls import path, include
from user import views as user_views
from django.contrib.auth import views as authentication_views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers, permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

router = routers.SimpleRouter()
router.register('products', ProductViewSet, basename='products')
router.register('loginAPI', LoginAPIView, basename='loginAPI')
router.register('logoutAPI', LogOutAPIView, basename='logoutAPI')
router.register('user', LoggedInUser, basename='logged_in_user')
schema_view = get_schema_view(
    openapi.Info(
        title="BritishDenimAPI",
        default_version='v 1.0',
        description="British Denim API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@ketengo.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
app_name = 'britishdenim'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    # path('accounts/', include('rest_framework.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    # path('auth/login/', views.LoginView.as_view(), name='loginView'),
    # path('auth/logout/', views.LogOutView, name='logoutView'),
    path('register/<sku>', views.register, name='register' ),
    path('sku_feed/<sku>', views.skuFeed, name='sku_feed' ),
    path('profile/', user_views.profile, name='profile'),
    path('signin/', user_views.signin, name='signin'),
    path('login/', user_views.LoginView.as_view(), name='login'),
    path('logout/', views.LogOutView, name='logout'),
    path('', views.index, name='index'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('rewards/', views.rewards, name= 'rewards'),
    path('stats/', views.stats, name= 'stats'),
    path('charts/', views.charts, name= 'charts'),
    path('consumer/', views.consumer, name= 'consumer'),
    path('consumer/<int:consumer_id>/invite/', views.invite_consumer_to_post, name='invite_consumer_to_post'),
    path('doc', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

urlpatterns += [
    # ... the rest of your URLconf goes here ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
