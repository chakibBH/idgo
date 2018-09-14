# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-09-13 07:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0060_auto_20180906_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='jurisdiction',
            name='communes',
            field=models.ManyToManyField(related_name='jurisdiction_communes', through='idgo_admin.JurisdictionCommune', to='idgo_admin.Commune', verbose_name='Communes'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='ogc_services',
            field=models.BooleanField(default=True, verbose_name='Services OGC'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='restricted_level',
            field=models.CharField(blank=True, choices=[('0', 'Tous les utilisateurs'), ('1', 'Utilisateurs authentifiés'), ('2', 'Utilisateurs authentifiés avec droits spécifiques'), ('3', 'Utilisateurs de cette organisation uniquement'), ('4', 'Organisations spécifiées')], default='0', max_length=20, null=True, verbose_name="Restriction d'accès"),
        ),
    ]