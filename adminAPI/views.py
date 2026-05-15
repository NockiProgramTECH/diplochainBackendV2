from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from diplomas.models import Diploma
from universities.models import University
from .serializers import DiplomaSerializer, UniversitySerializer


class DiplomaViewSet(viewsets.ModelViewSet):
    queryset = Diploma.objects.all()
    serializer_class = DiplomaSerializer
    permission_classes = [IsAdminUser]


class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [IsAdminUser]
