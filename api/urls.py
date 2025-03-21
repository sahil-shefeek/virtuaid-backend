from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('auth/', include('authentication.urls')),
    path('associates/', include('associates.urls')),
    path('carehomes/', include('carehomes.urls')),
    path('carehome-managers/', include('carehomemanagers.urls')),
    path('feedbacks/', include('feedbacks.urls')),
    path('reports/', include('reports.urls')),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]