# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model

from rest_framework import serializers

from knowledge_base.core.api.serializers import ModelSerializer
from knowledge_base.posts.models import Area, Post, Subject


class AreaSerializer(ModelSerializer):
    class Meta:
        model = Area
        fields = (
            'id',
            'name',
            'description',
            'thumbnail',
        )


class AreaURISerializer(ModelSerializer):
    custom_kwargs = {
        "pk": ['pk'],
    }

    class Meta:
        model = Area
        fields = (
            'id',
            'name',
            'description',
            'thumbnail',
            'resource_uri'
        )


class SubjectSerializer(ModelSerializer):
    area = AreaURISerializer()

    class Meta:
        model = Subject
        fields = (
            'id',
            'name',
            'description',
            'area',
        )


class SubjectURISerializer(ModelSerializer):
    custom_kwargs = {
        "pk": ['pk'],
        "area_pk": ['area', 'pk'],
    }
    parent_ids = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = (
            'id',
            'name',
            'description',
            'resource_uri',
            'parent_ids',
        )

    def get_parent_ids(self, instance):
        """
        When using nested endpoints, is useful to provide nested id values,
        instead of request every endpoint in every nested level.
        """
        return {
            "area_id": instance.area.id
        }


class PostSerializer(ModelSerializer):
    # To avoid cross importation.
    from knowledge_base.users.serializers import (
        ProfileURISerializer,
        SearchUserSerializer
    )

    subject = SubjectURISerializer()
    author = ProfileURISerializer()
    available_to = SearchUserSerializer(many=True)

    class Meta:
        model = Post
        fields = (
            'id',
            'name',
            'resume',
            'content',
            'author',
            'subject',
            'is_active',
            'created_date',
            'last_modified',
            'available_to',
        )


class PostURISerializer(ModelSerializer):
    custom_kwargs = {
        "pk": ['pk'],
        "subject_pk": ['subject', 'pk'],
        "area_pk": ['subject', 'area', 'pk'],
    }
    parent_ids = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id',
            'name',
            'resume',
            'parent_ids',
            'resource_uri',
            'is_active',
        )

    def get_parent_ids(self, instance):
        """
        When using nested endpoints, is useful to provide nested id values,
        instead of request every endpoint in every nested level.
        """
        return {
            "area_id": instance.subject.area.id,
            "subject_id": instance.subject.id
        }


class PostCreateSerializer(ModelSerializer):
    list_available_to = serializers.ListField(
        required=False
    )

    class Meta:
        model = Post
        fields = (
            'id',
            'name',
            'resume',
            'content',
            'author',
            'subject',
            'is_active',
            'list_available_to',
        )

    def create(self, validated_data):
        list_available_to = validated_data.pop('list_available_to', None)

        instance = super(PostCreateSerializer, self).create(validated_data)

        if list_available_to:
            user_model = get_user_model()
            users = user_model.objects.filter(
                id__in=list_available_to
            )

            for user in users:
                instance.available_to.add(user)

        return instance

    def update(self, instance, validated_data):
        list_available_to = validated_data.pop('list_available_to', None)

        instance = super(PostCreateSerializer, self).update(
            instance,
            validated_data
        )

        #
        # Deleting current users to save new ones.
        #
        instance.available_to.through.objects.all().delete()
        if list_available_to:
            user_model = get_user_model()
            users = user_model.objects.filter(
                id__in=list_available_to
            )

            for user in users:
                instance.available_to.add(user)

        return instance


class PostDocSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = (
            'id',
            'name',
            'resume',
            'content',
            'subject',
            'is_active',
        )
