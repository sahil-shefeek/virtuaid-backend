from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentication.views import InterfaceUserViewSet, UserDetailView, CustomTokenObtainPairView, \
    CustomTokenRefreshView, CustomTokenVerifyView, CustomTokenBlacklistView

router = DefaultRouter()
router.register(r'users', InterfaceUserViewSet)

urlpatterns = [
    path("app/", include("dj_rest_auth.urls")),
    path("app/register/", include("dj_rest_auth.registration.urls")),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    path('user/', UserDetailView.as_view(), name='user_details'),
    path('logout/', CustomTokenBlacklistView.as_view(), name='logout'),
    path('', include(router.urls))
]
