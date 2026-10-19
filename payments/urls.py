from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PaymentMethodViewSet, PaymentProviderCallbackView

router = DefaultRouter()
router.register("", PaymentMethodViewSet, basename="payment-method")

urlpatterns = [
    path("provider-callback/", PaymentProviderCallbackView.as_view(), name="payment-callback"),
    *router.urls,
]
