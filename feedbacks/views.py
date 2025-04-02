from rest_framework import viewsets, filters
from rest_framework.response import Response

from carehome_managers.models import CarehomeManagers
from feedbacks.models import Feedback
from feedbacks.serializers import FeedbackSerializer


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

    # filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # filterset_fields = ['resident']
    # ordering_fields = ['session_date']

    def get_queryset(self):
        user = self.request.user

        # Filter based on user group
        if user.groups.filter(name='SuperAdmin').exists():
            return Feedback.objects.all()
        elif user.groups.filter(name='Admin').exists():
            return Feedback.objects.filter(resident__care_home__admin=user)
        elif user.groups.filter(name='Manager').exists():
            managed_carehomes = CarehomeManagers.objects.filter(manager=user).values_list('carehome', flat=True)
            return Feedback.objects.filter(resident__care_home__in=managed_carehomes)
        else:
            return Feedback.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        resident_id = request.query_params.get('resident', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        if resident_id:
            queryset = queryset.filter(resident__id=resident_id)

        if start_date and end_date:
            queryset = queryset.filter(session_date__range=[start_date, end_date])
        elif start_date:
            queryset = queryset.filter(session_date__gte=start_date)
        elif end_date:
            queryset = queryset.filter(session_date__lte=end_date)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
