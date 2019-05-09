# Copyright (c) 2017-2019 Datasud.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views import View

from mama_cas.compat import is_authenticated as mama_is_authenticated
from mama_cas.models import ProxyGrantingTicket as MamaProxyGrantingTicket
from mama_cas.models import ProxyTicket as MamaProxyTicket
from mama_cas.models import ServiceTicket as MamaServiceTicket
from mama_cas.utils import redirect as mama_redirect
from mama_cas.utils import to_bool as mama_to_bool
from mama_cas.views import LoginView as MamaLoginView
from mama_cas.views import LogoutView as MamaLogoutView

from auth_users.forms.account import SignInForm
from auth_users.forms.account import SignUpForm
from auth_users.forms.account import UpdateAccountForm
from auth_users.forms.account import UserDeleteForm
from auth_users.forms.account import UserForgetPassword
from auth_users.forms.account import UserResetPassword
from auth_users.models.gdpr import Gdpr
from auth_users.models.gdpr import GdprUser

from idgo_admin.ckan_module import CkanHandler
from idgo_admin.exceptions import CkanBaseError
from idgo_admin.models import AccountActions
from idgo_admin.models import LiaisonsContributeurs
from idgo_admin.models import LiaisonsReferents
from idgo_admin.models.mail import send_account_creation_confirmation_mail
from idgo_admin.models.mail import send_account_deletion_mail
from idgo_admin.models.mail import send_reset_password_link_to_user
from idgo_admin.models import Organisation
from idgo_admin.shortcuts import render_with_info_profile
from idgo_admin.views.organisation import contributor_subscribe_process
from idgo_admin.views.organisation import creation_process
from idgo_admin.views.organisation import member_subscribe_process
from idgo_admin.views.organisation import referent_subscribe_process
import uuid

User = get_user_model()

decorators = [csrf_exempt, login_required(login_url=settings.LOGIN_URL)]


@method_decorator(decorators[0], name='dispatch')
class PasswordManager(View):

    def get(self, request, process, key=None):
        if process == 'forget':
            template = 'idgo_admin/forgottenpassword.html'
            form = UserForgetPassword()
        else:
            try:
                uuid.UUID(key)
            except Exception:
                raise Http404

            if process == 'initiate':
                template = 'idgo_admin/initiatepassword.html'
                form = UserResetPassword()

            if process == 'reset':
                template = 'idgo_admin/resetpassword.html'
                form = UserResetPassword()

        return render(request, template, {'form': form})

    def post(self, request, process, key=None):

        if process == 'forget':
            template = 'idgo_admin/forgottenpassword.html'
            form = UserForgetPassword(data=request.POST)
            action = 'reset_password'
            if not form.is_valid():
                return render(request, template, {'form': form})

            try:
                user = User.objects.get(
                    email=form.cleaned_data["email"], is_active=True)
            except Exception:
                message = "Cette adresse n'est pas liée a un compte IDGO actif "
                return render(request, 'idgo_admin/message.html',
                              {'message': message}, status=200)
            forget_action, created = AccountActions.objects.get_or_create(
                user=user, action=action, closed=None)

            try:
                url = request.build_absolute_uri(reverse(
                    'auth_users:password_manager', kwargs={'process': 'reset', 'key': forget_action.key}))
                send_reset_password_link_to_user(forget_action.user, url)
            except Exception as e:
                message = ("Une erreur s'est produite lors de l'envoi du mail "
                           "de réinitialisation: {error}".format(error=e))

                status = 400
            else:
                message = ('Vous recevrez un e-mail de réinitialisation '
                           "de mot de passe d'ici quelques minutes. "
                           'Pour changer votre mot de passe, '
                           'cliquez sur le lien qui vous sera indiqué '
                           "dans les 48h après réception de l'e-mail.")
                status = 200
            finally:
                return render(request, 'idgo_admin/message.html',
                              {'message': message}, status=status)

        if process == 'initiate':
            template = 'idgo_admin/initiatepassword.html'
            form = UserResetPassword(data=request.POST)
            action = "set_password_admin"
            message_error = ("Une erreur s'est produite lors de l'initialisation "
                             "de votre mot de passe")
            message_success = 'Votre compte utilisateur a été initialisé.'

        if process == 'reset':
            template = 'idgo_admin/resetpassword.html'
            form = UserResetPassword(data=request.POST)
            action = "reset_password"
            message_error = ("Une erreur s'est produite lors de la réinitialisation "
                             "de votre mot de passe. Le jeton de réinitialisation "
                             "semble obsolète.")
            message_success = 'Votre mot de passe a été réinitialisé.'

        try:
            uuid.UUID(key)
        except Exception:
            raise Http404

        if not form.is_valid():
            return render(request, template,
                          {'form': form})

        try:
            generic_action = AccountActions.objects.get(
                key=key, action=action,
                user__username=form.cleaned_data.get('username'),
                closed=None)
        except Exception:
            message = message_error

            status = 400
            return render(request, 'idgo_admin/message.html',
                          {'message': message}, status=status)

        user = generic_action.user
        try:
            with transaction.atomic():
                user = form.save(request, user)
                generic_action.closed = timezone.now()
                generic_action.save()
        except ValidationError:
            return render(request, template, {'form': form})
        except IntegrityError:
            logout(request)
        except Exception:
            messages.error(
                request, message_error)
        else:
            messages.success(
                request, message_success)

        return HttpResponseRedirect(
            reverse('auth_users:update_account'))


@login_required(login_url=settings.LOGIN_URL)
@csrf_exempt
def delete_account(request):

    user = request.user
    if request.method == 'GET':
        return render_with_info_profile(
            request, 'idgo_admin/deleteaccount.html',
            {'uform': UserDeleteForm()})

    uform = UserDeleteForm(data=request.POST)
    if not uform.is_valid():
        return render_with_info_profile(
            request, 'idgo_admin/deleteaccount.html', {'uform': uform})

    email = user.email
    full_name = user.get_full_name()
    username = user.username

    logout(request)
    user.delete()

    send_account_deletion_mail(email, full_name, username)

    return render(request, 'idgo_admin/message.html', status=200,
                  context={'message': 'Votre compte a été supprimé.'})


@method_decorator(decorators, name='dispatch')
class ReferentAccountManager(View):

    def delete(self, request, *args, **kwargs):

        # TODO Better

        user = request.user

        organisation_id = request.GET.get('organisation')
        username = request.GET.get('username')
        target = request.GET.get('target')
        if not organisation_id or not username or target not in ['members', 'contributors', 'referents']:
            raise Http404()

        user = get_object_or_404(User, username=username)
        organisation = get_object_or_404(Organisation, id=organisation_id)
        if user.get_roles(organisation=organisation)["is_referent"] and not user.is_admin:
            return HttpResponseForbidden()

        if target == 'members':
            if user.organisation != organisation:
                raise Http404()

            user.organisation = None
            user.membership = False
            user.save()
            message = "L'utilisateur <strong>{0}</strong> n'est plus membre de <strong>{1}</strong>.".format(username, organisation.legal_name)
            messages.success(request, message)

        if target == 'contributors':
            instance = get_object_or_404(LiaisonsContributeurs, user=user, organisation=organisation)
            instance.delete()
            message = "L'utilisateur <strong>{0}</strong> n'est plus contributeur de <strong>{1}</strong>.".format(username, organisation.legal_name)
            messages.success(request, message)

        if target == 'referents' and user.is_admin:
            instance = get_object_or_404(LiaisonsReferents, user=user, organisation=organisation)
            instance.delete()
            message = "L'utilisateur <strong>{0}</strong> n'est plus référent technique de <strong>{1}</strong>.".format(username, organisation.legal_name)
            messages.success(request, message)

        return HttpResponse(status=200)


@method_decorator(decorators[0], name='dispatch')
class SignUp(View):
    template = 'auth_users/signup.html'

    @staticmethod
    def sign_up_process(request, user, mail=True):
        action = AccountActions.objects.create(user=user, action='confirm_mail')
        if mail:
            url = request.build_absolute_uri(
                reverse('idgo_admin:confirmation_mail', kwargs={'key': action.key}))
            send_account_creation_confirmation_mail(action.user, url)

    @staticmethod
    def gdpr_aggrement(user, terms_and_conditions):
        if not terms_and_conditions:
            raise IntegrityError
        try:
            GdprUser.objects.create(
                user=user, gdpr=Gdpr.objects.latest('issue_date')
            )
        except Exception:
            raise IntegrityError

    def get(self, request):
        return render(request, self.template, {'form': SignUpForm()})

    @transaction.atomic
    def post(self, request):

        form = SignUpForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, self.template, context={'form': form})

        try:
            with transaction.atomic():

                user = User.objects.create_user(**form.cleaned_user_data)

                if form.create_organisation:
                    kvp = {}
                    for k, v in form.cleaned_organisation_data.items():
                        if k.startswith('org_'):
                            k = k[4:]
                        kvp[k] = v
                    organisation = Organisation.objects.create(**kvp)
                else:
                    organisation = form.cleaned_user_data['organisation']
                user.organisation = organisation
                user.save(update_fields=['organisation', ])

                self.gdpr_aggrement(
                    user, form.cleaned_data.get('terms_and_conditions', False)
                )

                CkanHandler.add_user(user, form.cleaned_user_data['password'])
        except ValidationError as e:
            messages.error(request, e.message)
            return render(request, self.template, context={'form': form})
        except CkanBaseError as e:
            form.add_error('__all__', e.__str__())
            messages.error(request, e.__str__())
            return render(request, self.template, context={'form': form})

        # else:
        self.sign_up_process(request, user)

        if form.create_organisation:
            creation_process(request, user, organisation, mail=False)

        if form.is_member:
            member_subscribe_process(request, user, organisation, mail=False)

        # Dans le cas ou seul le role de contributeur est demandé
        if form.is_contributor and not form.is_referent:
            contributor_subscribe_process(request, user, organisation, mail=False)

        # role de référent requis donc role de contributeur requis
        if form.is_referent:
            referent_subscribe_process(request, user, organisation, mail=False)

        message = ('Votre compte a bien été créé. Vous recevrez un e-mail '
                   "de confirmation d'ici quelques minutes. Pour activer "
                   'votre compte, cliquez sur le lien qui vous sera indiqué '
                   "dans les 48h après réception de l'e-mail.")

        return render(request, 'idgo_admin/message.html',
                      context={'message': message}, status=200)


@method_decorator(decorators, name='dispatch')
class UpdateAccount(View):
    template = 'idgo_admin/updateaccount.html'

    def get(self, request):
        user = request.user
        return render_with_info_profile(
            request, self.template, {'form': UpdateAccountForm(instance=user)})

    @transaction.atomic
    def post(self, request):
        user = request.user
        form = UpdateAccountForm(request.POST, instance=user)

        if not form.is_valid():
            return render_with_info_profile(
                request, self.template, context={'form': form})

        try:
            with transaction.atomic():

                if form.new_password:
                    user.set_password(form.new_password)
                    user.save()
                    logout(request)
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                for field in form.Meta.user_fields:
                    setattr(user, field, form.cleaned_data[field])
                user.save()

                CkanHandler.update_user(user)

        except ValidationError as e:
            messages.error(request, e.message)
            return render_with_info_profile(
                request, self.template, context={'form': form})
        except CkanBaseError as e:
            form.add_error('__all__', e.__str__())
            messages.error(request, e.__str__())
            return render_with_info_profile(
                request, self.template, context={'form': form})

        messages.success(request, 'Votre compte a bien été mis à jour.')

        return render_with_info_profile(
            request, self.template, context={'form': form}, status=200)


@login_required(login_url=settings.LOGIN_URL)
@csrf_exempt
def create_sftp_account(request):

    user = request.user

    try:
        user.create_ftp_account()
    except Exception as e:
        print(e)
        # TODO: Géré les exceptions
        messages.error(
            request, 'Une erreur est survenue lors de la création de votre compte FTP.')
    else:
        messages.success(request, (
            'Le compte FTP a été créé avec succès. '
            "Le processus d'activation peut prendre quelques minutes. "
            'Un mot de passe a été généré automatiquement. '
            "Celui-ci n'est pas modifiable."))

    return HttpResponseRedirect(reverse('auth_users:update_account'))


@login_required(login_url=settings.LOGIN_URL)
@csrf_exempt
def delete_sftp_account(request):

    user = request.user

    try:
        user.delete_ftp_account()
    except Exception as e:
        print(e)
        # TODO: Géré les exceptions
        messages.error(
            request, 'Une erreur est survenue lors de la suppression de votre compte FTP.')
    else:
        messages.success(request, 'Le compte FTP a été supprimé avec succès.')

    return HttpResponseRedirect(reverse('auth_users:update_account'))


@method_decorator(csrf_exempt, name='dispatch')
class SignIn(MamaLoginView):

    template_name = 'auth_users/signin.html'
    form_class = SignInForm

    def get(self, request, *args, **kwargs):
        service = request.GET.get('service')
        gateway = mama_to_bool(request.GET.get('gateway'))
        if gateway and service:
            if mama_is_authenticated(request.user):
                st = MamaServiceTicket.objects.create_ticket(
                    service=service, user=request.user)
                if self.warn_user():
                    return mama_redirect('cas_warn', params={'service': service, 'ticket': st.ticket})
                return mama_redirect(service, params={'ticket': st.ticket})
            else:
                return mama_redirect(service)
        elif mama_is_authenticated(request.user):
            if service:
                st = MamaServiceTicket.objects.create_ticket(service=service, user=request.user)
                if self.warn_user():
                    return mama_redirect('cas_warn', params={'service': service, 'ticket': st.ticket})
                return mama_redirect(service, params={'ticket': st.ticket})
            # else:
            #     msg = "Vous êtes connecté comme <strong>{username}</strong>".format(
            #         username=request.user.username)
            #     messages.success(request, msg)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.user)

        if form.cleaned_data.get('warn'):
            self.request.session['warn'] = True

        service = self.request.GET.get('service')
        if service:
            st = MamaServiceTicket.objects.create_ticket(
                service=service, user=self.request.user, primary=True)
            return mama_redirect(service, params={'ticket': st.ticket})

        nxt_pth = self.request.GET.get('next', None)
        if nxt_pth:
            return HttpResponseRedirect(nxt_pth)
        return mama_redirect('idgo_admin:list_my_datasets')


def logout_user(request):
    if mama_is_authenticated(request.user):
        MamaServiceTicket.objects.consume_tickets(request.user)
        MamaProxyTicket.objects.consume_tickets(request.user)
        MamaProxyGrantingTicket.objects.consume_tickets(request.user)
        MamaServiceTicket.objects.request_sign_out(request.user)
        logout(request)


class SignOut(MamaLogoutView):

    def get(self, request, *args, **kwargs):
        service = request.GET.get('service')
        if not service:
            service = request.GET.get('url')
        follow_url = getattr(settings, 'MAMA_CAS_FOLLOW_LOGOUT_URL', True)
        logout_user(request)
        if service and follow_url:
            return mama_redirect(service)
        return mama_redirect('auth_users:signIn')
