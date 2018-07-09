# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-07-09 09:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0044_auto_20180604_1637'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='extractable',
            field=models.BooleanField(default=True, verbose_name='Extractible'),
        ),
        migrations.AddField(
            model_name='resource',
            name='ogc_services',
            field=models.BooleanField(default=True, verbose_name='Services OGC'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='contributions',
            field=models.ManyToManyField(related_name='profile_contributions', through='idgo_admin.LiaisonsContributeurs', to='idgo_admin.Organisation', verbose_name="Organisations dont l'utilisateur est contributeur"),
        ),
        migrations.AlterField(
            model_name='profile',
            name='referents',
            field=models.ManyToManyField(related_name='profile_referents', through='idgo_admin.LiaisonsReferents', to='idgo_admin.Organisation', verbose_name="Organisations dont l'utilisateur est réferent"),
        ),
    ]
