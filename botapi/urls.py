"""botapi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.contrib.auth import views
from api.forms import LoginForm

urlpatterns = [
    url(r'', include('api.urls')),
    url(r'^multi/', include('twitchstreams.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', views.login, {'template_name': 'login.html', 'authentication_form': LoginForm}, name='login'),
    url(r'^logout/$', views.logout, {'next_page': '/login'}),
#    url(r'^forum/', include('paiji2_forum.urls')),
]
#urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
#if settings.DEBUG:
#   urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
#   urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
