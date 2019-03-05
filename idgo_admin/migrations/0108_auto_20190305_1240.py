# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-03-05 11:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0107_auto_20190305_1225'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='organisation',
            options={'ordering': ['slug'], 'verbose_name': 'Organisation', 'verbose_name_plural': 'Organisations'},
        ),
        migrations.AlterField(
            model_name='organisation',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Adresse e-mail'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='name',
            field=models.CharField(db_index=True, max_length=100, unique=True, verbose_name='Dénomination sociale'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='slug',
            field=models.SlugField(max_length=100, unique=True, verbose_name='Slug'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='website',
            field=models.URLField(blank=True, verbose_name='Site internet'),
        ),
    ]