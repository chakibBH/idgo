# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-07 10:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0014_auto_20171130_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='picto',
            field=models.ImageField(blank=True, null=True, upload_to='logo/', verbose_name='Pictogramme'),
        ),
    ]