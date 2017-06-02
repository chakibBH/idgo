from django.conf.urls import url


from profiles.views import confirmation_email, delete_account, modify_account, \
                           sign_in, sign_out, sign_up, main, activation_admin, publish_request


urlpatterns = [
    url(r'^$', main, name='main'),
    url(r'^signin/?$', sign_in, name='signIn'),
    url(r'^signout/?$', sign_out, name='signOut'),
    url(r'^signup/?$', sign_up, name='signUp'),
    url(r'^confirmation_email/(?P<key>.+)/?$', confirmation_email, name='confirmation_mail'),
    url(r'^activation_admin/(?P<key>.+)/?$', activation_admin,  name='activation_admin'),
    url(r'^modifyaccount/?$', modify_account, name='modifyAccount'),
    url(r'^manage_publication/?$', publish_manager, name='publish_manager'),
    url(r'^publish_request/(?P<key>.+)/?$', publish_request, name='publish_request'),
    url(r'^deleteaccount/?$', delete_account, name='deleteAccount')
]
