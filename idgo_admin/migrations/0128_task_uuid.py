# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-04-23 14:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0127_mappingcategory_mappinglicence'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='uuid',
            field=models.UUIDField(blank=True, db_index=True, editable=False, null=True, unique=True, verbose_name='Id'),
        ),
    ]
