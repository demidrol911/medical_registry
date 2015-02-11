from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    url(r'^index/$', views.index),
    url(r'^json/periods/$', views.get_periods_json),
    url(r'^json/registries/$', views.get_registers_json),
    url(r'^json/services/$', views.get_services_json)
)