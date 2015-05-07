from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    url(r'^index/$', views.index),
    url(r'^json/periods/$', views.get_periods_json),
    url(r'^json/organization-registries/$',
        views.get_organization_registers_json),
    url(r'^json/organization-registries/update/$',
        views.update_organization_registry_status),
    url(r'^json/department-registries/$',
        views.get_department_registers_json),
    url(r'^json/services/$', views.get_services_json),
    url(r'^json/statuses/$', views.get_registry_status_json),
    url(r'^json/additional-info/$', views.get_additional_info_json),
)