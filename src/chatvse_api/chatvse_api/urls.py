from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static

from .views import chat_proxy


urlpatterns = [
    path('admin/', admin.site.urls),

    path('chat/', chat_proxy)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)