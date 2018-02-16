# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-13 10:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0034_auto_20180213_1156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountactions',
            name='action',
            field=models.CharField(blank=True, choices=[('confirm_mail', "Confirmation de l'email par l'utilisateur"), ('confirm_new_organisation', "Confirmation par un administrateur de la création d'une organisation par l'utilisateur"), ('confirm_rattachement', "Rattachement d'un utilisateur à une organisation par un administrateur"), ('confirm_referent', "Confirmation du rôle de réferent d'une organisation pour un utilisateur par un administrateur"), ('confirm_contribution', "Confirmation du rôle de contributeur d'une organisation pour un utilisateur par un administrateur"), ('reset_password', 'Réinitialisation du mot de passe'), ('set_password_admin', 'Initialisation du mot de passe suite à une inscription par un administrateur')], default='confirm_mail', max_length=250, null=True, verbose_name='Action de gestion de profile'),
        ),
    ]