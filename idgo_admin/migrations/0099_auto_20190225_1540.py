# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-02-25 14:40
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0098_auto_20190219_0954'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='license',
            options={'verbose_name': 'Licence', 'verbose_name_plural': 'Licences'},
        ),
        migrations.AddField(
            model_name='license',
            name='alternate_titles',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), null=True, size=None),
        ),
        migrations.AddField(
            model_name='license',
            name='alternate_urls',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.URLField(), null=True, size=None),
        ),
        migrations.AddField(
            model_name='license',
            name='slug',
            field=models.SlugField(null=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='maintainer',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='od_conformance',
            field=models.CharField(default='approved', max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='osd_conformance',
            field=models.CharField(default='not reviewed', max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='license',
            name='status',
            field=models.CharField(default='active', max_length=30),
        ),
        migrations.AlterField(
            model_name='license',
            name='title',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='license',
            name='url',
            field=models.URLField(blank=True),
        ),
    ]