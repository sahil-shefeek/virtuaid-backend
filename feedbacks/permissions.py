from rest_framework.permissions import BasePermission


class FeedbackPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated

    def filter_queryset(self, request, queryset, view):
        user = request.user
        if user.groups.filter(name='SuperAdmin').exists():
            return queryset
        elif user.groups.filter(name='Admin').exists():
            return queryset.filter(
                associate__care_home__admin=user
            )
        elif user.groups.filter(name='Manager').exists():
            return queryset.filter(
                associate__care_home__carehomemanagers__manager=user
            )
        return queryset.none()
