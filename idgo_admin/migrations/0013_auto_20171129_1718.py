# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-29 16:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0012_auto_20171128_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='dl_url',
            field=models.URLField(blank=True, max_length=2000, null=True, verbose_name='Télécharger depuis une URL'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='referenced_url',
            field=models.URLField(blank=True, max_length=2000, null=True, verbose_name='Référencer une URL'),
        ),
    ]
