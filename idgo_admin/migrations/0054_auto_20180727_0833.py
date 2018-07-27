# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-07-27 06:33
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0053_dataset_bbox'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='bbox',
            field=django.contrib.gis.db.models.fields.PolygonField(blank=True, null=True, srid=4171, verbose_name='Rectangle englobant'),
        ),
    ]