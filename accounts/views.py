import secrets
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PhoneVerification, User
from .serializers import RegistrationSerializer, UserSerializer
from .services import deliver_otp
from .validators import normalize_phone
from core.providers import ProviderUnavailable

class AuthRegisterView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
            },
            status=status.HTTP_201_CREATED,
        )


class AuthLoginView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        password = request.data.get("password", "")
        if not email or not isinstance(password, str):
            raise ValidationError({"detail": "Email and password are required."})
        user = authenticate(request=request, email=email, password=password)
        if user is None:
            raise ValidationError({"detail": "The email or password is incorrect."})
        requested_role = request.data.get("role")
        if requested_role and requested_role != user.role:
            raise PermissionDenied("This account does not have the requested role.")
        if user.role == User.Role.ADMIN and not user.is_staff:
            raise PermissionDenied("Administrator access has not been enabled for this account.")
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
            }
        )


class CurrentUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class OtpRequestView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "otp"

    def post(self, request):
        phone_number = normalize_phone(request.data.get("phone_number", ""))
        now = timezone.now()
        latest = PhoneVerification.objects.filter(
            phone_number=phone_number, created_at__gte=now - timedelta(minutes=1)
        ).first()
        if latest:
            raise ValidationError({"detail": "Wait one minute before requesting another code."})
        code = f"{secrets.randbelow(10000):04d}"
        verification = PhoneVerification.objects.create(
            phone_number=phone_number,
            code_hash=make_password(code),
            expires_at=now + timedelta(minutes=5),
        )
        try:
            expose_code = deliver_otp(phone_number, code)
        except ProviderUnavailable:
            verification.delete()
            raise
        response_data = {
            "detail": "Verification code sent.",
            "expires_in_seconds": 300,
            "verification_id": verification.id,
        }
        if expose_code:
            response_data["debug_code"] = code
        return Response(response_data, status=status.HTTP_202_ACCEPTED)


class OtpVerifyView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "otp"

    def post(self, request):
        phone_number = normalize_phone(request.data.get("phone_number", ""))
        code = str(request.data.get("code", ""))
        verification = PhoneVerification.objects.filter(
            phone_number=phone_number, verified_at__isnull=True
        ).first()
        if not verification or verification.expires_at <= timezone.now():
            raise ValidationError({"code": "The code is invalid or has expired."})
        if verification.attempts >= 5:
            raise ValidationError({"code": "Too many attempts. Request a new code."})
        verification.attempts += 1
        if not check_password(code, verification.code_hash):
            verification.save(update_fields=("attempts",))
            raise ValidationError({"code": "The verification code is incorrect."})
        verification.verified_at = timezone.now()
        verification.save(update_fields=("attempts", "verified_at"))
        User.objects.filter(phone_number=phone_number).update(phone_verified=True)
        return Response({"verified": True, "phone_number": phone_number})
