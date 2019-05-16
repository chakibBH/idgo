# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-05-09 13:19
from __future__ import unicode_literals

import auth_users.managers
from django.conf import settings
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('phone', models.CharField(blank=True, max_length=10, null=True, verbose_name='Téléphone')),
                ('is_active', models.BooleanField(default=False, verbose_name='Validation suite à confirmation mail par utilisateur')),
                ('membership', models.BooleanField(default=False, verbose_name='Utilisateur rattaché à une organisation')),
                ('crige_membership', models.BooleanField(default=False, verbose_name='Utilisateur affilié au CRIGE')),
                ('is_admin', models.BooleanField(default=False, verbose_name='Administrateur métier')),
                ('sftp_password', models.CharField(blank=True, max_length=10, null=True, verbose_name='Mot de passe sFTP')),
                ('user_old_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='Ancien id user')),
                ('profile_old_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='Ancien id profil')),
            ],
            options={
                'verbose_name': 'Profil utilisateur',
                'verbose_name_plural': 'Profils des utilisateurs',
            },
            managers=[
                ('objects', auth_users.managers.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Gdpr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(verbose_name='Title')),
                ('description', models.TextField(verbose_name='Description')),
                ('issue_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date d'émission")),
            ],
            options={
                'get_latest_by': 'issue_date',
                'verbose_name': "Modalité et condition d'utilisation (RGPD)",
                'verbose_name_plural': "Modalités et conditions d'utilisation (RGPD)",
            },
        ),
        migrations.CreateModel(
            name='GdprUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('validated_on', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True, verbose_name='Date de validation')),
                ('gdpr', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth_users.Gdpr', verbose_name='RGPD')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'RGPD / Utilisateur',
            },
        ),
    ]