from rest_framework import serializers
from diplomas.models import Diploma
from universities.models import University


class DiplomaSerializer(serializers.ModelSerializer):
    university_name = serializers.CharField(source='university.name', read_only=True)
    university_acronym = serializers.CharField(source='university.acronym', read_only=True)

    class Meta:
        model = Diploma
        fields = '__all__'


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'private_key_pem': {'write_only': True},
        }