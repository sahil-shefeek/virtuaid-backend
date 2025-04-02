import os
import uuid
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, permissions, parsers, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .models import Video
from .serializers import VideoSerializer, VideoInitSerializer, ChunkUploadSerializer

class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'title']
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user.is_superadmin:
            if user.is_admin:
                queryset = queryset.filter(resident__care_home__admin=user)
            elif user.is_manager:
                queryset = queryset.filter(resident__care_home__carehomemanagers__manager=user)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save()
