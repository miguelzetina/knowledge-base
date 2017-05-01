# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-28 21:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20170428_1632'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subject',
            name='area',
        ),
        migrations.AddField(
            model_name='subject',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='posts.Category'),
        ),
    ]
