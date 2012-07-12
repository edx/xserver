from django.conf.urls import patterns, include, url

urlpatterns = patterns('queue.views',
	url(r'^submit/$', 'submit'),
	url(r'^get_info/$', 'get_info'),
)
