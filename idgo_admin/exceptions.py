from django.core.handlers.wsgi import WSGIRequest
from functools import wraps


class GenericException(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return str(self.args)


class CriticalException(GenericException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ConflictError(GenericException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FakeError(GenericException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SizeLimitExceededError(GenericException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ExceptionsHandler(object):

    template_html_500 = 'idgo_admin/servererror.html'

    MESSAGES = {
        'CkanTimeoutError': 'Impossible de joindre le serveur CKAN.'}

    def __init__(self, ignore=None):
        self.ignore = ignore or []

    def __call__(self, f):

        @wraps(f)
        def wrapper(*args, **kwargs):
            request = None
            args = list(args)
            for arg in args:
                if isinstance(arg, WSGIRequest):
                    request = arg
            try:
                return f(*args, **kwargs)
            except Exception as e:
                if self.is_ignored(e):
                    return f(*args, **kwargs)
                raise e
                # qualname = e.__class__.__qualname__
                # context = {
                #     'message': self.MESSAGES.get(qualname)}
                #
                # if request:
                #     return render(request, self.template_html_500,
                #                   context=context, status=500)
                # return HttpResponseServerError()

        return wrapper

    def is_ignored(self, exception):
        return type(exception) in self.ignore
