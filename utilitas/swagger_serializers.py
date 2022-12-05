from rest_framework import serializers


class FilterSerializer(serializers.Serializer):
    field_name = serializers.CharField(max_length=25)
    operator = serializers.CharField(max_length=25)
    value = serializers.CharField(max_length=25)


class FilterParamsSerializer(serializers.Serializer):
    filter_params = FilterSerializer(many=True)