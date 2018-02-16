# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-07 11:02
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0024_auto_20180131_0927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='categories',
            field=models.ManyToManyField(blank=True, to='idgo_admin.Category', verbose_name="Catégories d'appartenance"),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='ckan_id',
            field=models.UUIDField(blank=True, db_index=True, null=True, unique=True, verbose_name='Identifiant CKAN'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='ckan_slug',
            field=models.SlugField(blank=True, max_length=100, null=True, unique=True, verbose_name='Label court'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='data_type',
            field=models.ManyToManyField(blank=True, to='idgo_admin.DataType', verbose_name='Type de données'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='date_creation',
            field=models.DateField(blank=True, null=True, verbose_name='Date de création'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='date_modification',
            field=models.DateField(blank=True, null=True, verbose_name='Date de dernière modification'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='date_publication',
            field=models.DateField(blank=True, null=True, verbose_name='Date de publication'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='editor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Producteur (propriétaire)'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='geonet_id',
            field=models.UUIDField(blank=True, db_index=True, null=True, unique=True, verbose_name='UUID de la métadonnées'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='is_inspire',
            field=models.BooleanField(default=False, verbose_name='Le jeu de données est soumis à la règlementation INSPIRE'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='keywords',
            field=taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Liste de mots-clés'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='license',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='idgo_admin.License', verbose_name='Licence'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Titre'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='organisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='idgo_admin.Organisation', verbose_name='Organisation à laquelle est rattaché ce jeu de données'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='owner_email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='E-mail du producteur'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='published',
            field=models.BooleanField(default=False, verbose_name='Publier le jeu de données'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to='thumbnails/', verbose_name='Illustration'),
        ),
    ]