# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-03-05 11:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0106_auto_20190305_1209'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='resource',
            options={'verbose_name': 'Ressource', 'verbose_name_plural': 'Ressources'},
        ),
        migrations.RenameField(
            model_name='dataset',
            old_name='update_freq',
            new_name='update_frequency',
        ),
    ]
