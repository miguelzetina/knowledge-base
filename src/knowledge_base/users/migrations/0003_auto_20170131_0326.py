# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-01-31 03:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20170122_2154'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='activation_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='favorite_subjects',
            field=models.ManyToManyField(blank=True, to='posts.Subject'),
        ),
    ]