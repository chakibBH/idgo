# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-12 10:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0030_auto_20180212_1104'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='custom_frequency',
            field=models.PositiveIntegerField(default=0, verbose_name='Nombre de jours entre chaque synchronisations'),
        ),
    ]
