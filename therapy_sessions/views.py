from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import TherapySession
from .serializers import SessionSerializer, SessionCreateUpdateSerializer
from django.utils import timezone

class SessionViewSet(viewsets.ModelViewSet):
    queryset = TherapySession.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'resident']
    search_fields = ['resident__name', 'notes']
    ordering_fields = ['scheduled_date', 'created_at', 'updated_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SessionCreateUpdateSerializer
        return SessionSerializer
    
    def get_queryset(self):
        queryset = TherapySession.objects.all()
        
        # Filter by status categories
        status_category = self.request.query_params.get('status_category', None)
        now = timezone.now()
        
        if status_category == 'completed':
            queryset = queryset.filter(status='completed')
        elif status_category == 'upcoming':
            queryset = queryset.filter(status='scheduled', scheduled_date__gt=now)
        elif status_category == 'past_due':
            queryset = queryset.filter(status='scheduled', scheduled_date__lt=now)
        elif status_category == 'in_progress':
            queryset = queryset.filter(status='in_progress')
        elif status_category == 'today':
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start.replace(hour=23, minute=59, second=59)
            queryset = queryset.filter(scheduled_date__range=(today_start, today_end))
        
        # Filter by feedback status
        feedback_status = self.request.query_params.get('feedback_status', None)
        if feedback_status == 'completed':
            queryset = queryset.exclude(feedback=None)
        elif feedback_status == 'pending':
            queryset = queryset.filter(status='completed', feedback=None)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        session = self.get_object()
        session.status = 'completed'
        session.end_time = timezone.now()
        session.save()
        return Response({'status': 'Session marked as completed'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def mark_in_progress(self, request, pk=None):
        session = self.get_object()
        session.status = 'in_progress'
        session.save()
        return Response({'status': 'Session marked as in progress'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def cancel_session(self, request, pk=None):
        session = self.get_object()
        session.status = 'cancelled'
        session.save()
        return Response({'status': 'Session cancelled'}, status=status.HTTP_200_OK)
