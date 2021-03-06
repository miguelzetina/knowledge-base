# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-08 03:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('posts', '0005_auto_20170327_1404'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='editable_to',
            field=models.ManyToManyField(blank=True, related_name='editable_posts', to=settings.AUTH_USER_MODEL, verbose_name=b'users who can edit the post.'),
        ),
        migrations.AlterField(
            model_name='post',
            name='available_to',
            field=models.ManyToManyField(blank=True, related_name='available_posts', to=settings.AUTH_USER_MODEL, verbose_name=b'users who can view the post.'),
        ),
    ]
