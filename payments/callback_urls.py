from django.urls import path

from .views import PaymentProviderCallbackView

urlpatterns = [
    path("", PaymentProviderCallbackView.as_view(), name="payment-callback"),
]
