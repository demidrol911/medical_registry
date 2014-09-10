from django.conf.urls import patterns, include, url
from django.conf import settings
from complaint import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.home),
    url(r'^(?P<complaint_type>consultation|complain|expertise)/$', views.home),
    url(r'^new/$', views.new),
    url(r'^(?P<complaint_id>\d+)/edit/$', views.edit),
    url(r'^edit/$', views.edit)
    )