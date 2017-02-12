# log/urls.py
from django.conf.urls import url
from . import views

# We are adding a URL called /home
urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^home/?$', views.home, name='home'),
    url(r'^redirect/?$', views.redirect, name='redirect'),
    url(r'^discord/?$', views.verify, name='verify'),
    url(r'^map/?$', views.get_map, name='get_map'),
    url(r'^join/?$', views.join, name='join'),
    url(r'^leave/?$', views.leave, name='leave'),
    url(r'^picking/?$', views.picking, name='picking'),
    url(r'^here/?$', views.here, name='here'),
    url(r'^captain/?$', views.captain, name='captain'),
    url(r'^check_captains/?$', views.check_captains, name='check_captains'),
    url(r'^get_mutator/?$', views.get_mutator, name='get_mutator'),
    url(r'^pug_all/?$', views.list_all, name='list_all'),
    url(r'^list_mode/?$', views.listing, name='listing'),
    url(r'^list_maps/?$', views.list_maps, name='list_maps'),
    url(r'^tag/?$', views.set_tag, name='set_tag'),
]
