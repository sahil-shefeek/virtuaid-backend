from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('auth/', include('authentication.urls')),
    path('residents/', include('residents.urls')),
    path('carehomes/', include('carehomes.urls')),
    path('carehome-managers/', include('carehome_managers.urls')),
    path('feedbacks/', include('feedbacks.urls')),
    path('reports/', include('reports.urls')),
    path('analysis/', include('analysis.urls')),
    path('therapy_sessions/', include('therapy_sessions.urls')),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]