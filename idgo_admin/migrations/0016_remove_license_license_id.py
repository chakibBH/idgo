# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-08 14:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0015_category_picto'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='license',
            name='license_id',
        ),
    ]