from django.conf import settings
from django.conf.urls import include, url
from . import views 
# Uncomment the next two lines to enable the admin:

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^getobject/type/(?P<obj_type>[a-zA-Z]+)/tag/(?P<obj_tag>[a-zA-Z0-9_\-]+)/index/(?P<obj_index>[0-9]+)/?$', views.get_object, name='get_object'),
    url(r'^updatestreams/?$', views.update_streams, name='update_streams'),
    url(r'^updatechannels/?$', views.update_channels, name='update_channels'),
    url(r'^livenow/?$', views.live_now, name='live_now'),
    url(r'^view/?$', views.view_streams, name='view_streams'),
    #url(r'^%sms-admin/' % settings.URL_INFIX, include(admin.site.urls)),
    url(r'^edit/(?P<streams_url>[a-zA-Z0-9_\-/]+)/?$', views.index, name='index'),
    url(r'^tag/(?P<tag>[a-zA-Z0-9_\-]+/)/?$', views.view_tag, name='view_tag'),
    url(r'^(?P<streams_url>[a-zA-Z0-9_\-/]+)/?$', views.view_streams, name='view_streams'),
    
    # Examples:
    # url(r'^$', 'twinstream.views.home', name='home'),
    # url(r'^twinstream/', include('twinstream.foo.urls')),
]
