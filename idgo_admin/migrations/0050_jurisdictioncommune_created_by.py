# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-07-19 10:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0049_auto_20180719_1205'),
    ]

    operations = [
        migrations.AddField(
            model_name='jurisdictioncommune',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='creates_jurisdiction', to='idgo_admin.Profile', verbose_name="Profil de l'utilisateur"),
        ),
    ]