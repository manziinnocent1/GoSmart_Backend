from django.urls import path

from .views import AuthLoginView, AuthRegisterView, CurrentUserView, OtpRequestView, OtpVerifyView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", AuthRegisterView.as_view(), name="register"),
    path("login/", AuthLoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("otp/request/", OtpRequestView.as_view(), name="otp-request"),
    path("otp/verify/", OtpVerifyView.as_view(), name="otp-verify"),
]
