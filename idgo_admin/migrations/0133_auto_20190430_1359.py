# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-04-30 11:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0132_remove_remoteckandataset_remote_organisation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='remotecsw',
            name='getrecords',
            field=models.TextField(blank=True, null=True, verbose_name='GetRecords'),
        ),
    ]
