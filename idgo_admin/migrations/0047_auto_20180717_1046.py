# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-07-17 08:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0046_auto_20180709_1529'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportedCrs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auth_name', models.CharField(default='EPSG', max_length=100, verbose_name='Authority Name')),
                ('auth_code', models.CharField(max_length=100, verbose_name='Authority Code')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
            ],
            options={
                'verbose_name_plural': "CRS supportés par l'application",
                'verbose_name': "CRS supporté par l'application",
                'db_table': 'supported_crs',
            },
        ),
        migrations.AddField(
            model_name='resource',
            name='crs',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='idgo_admin.SupportedCrs', verbose_name='CRS'),
        ),
    ]