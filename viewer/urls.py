from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    url(r'^registers$', views.index),
    url(r'^periods_list/$', views.periods_list),
)