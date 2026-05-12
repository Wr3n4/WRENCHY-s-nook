from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
#from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #+ debug_toolbar_urls