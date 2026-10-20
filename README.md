# GoSmart backend

Django REST API for the GoSmart passenger, driver, and operations screens.

## Feature apps

| App | Responsibility |
| --- | --- |
| `accounts` | User accounts, JWT authentication, profiles, and phone verification |
| `core` | Shared vehicle choices, health endpoint, saved places, and emergency alerts |
| `drivers` | Driver profiles, onboarding documents, ride preferences, earnings, and cash-outs |
| `rides` | Ride quotes, requests, matching, trip state, PINs, and ratings |
| `payments` | Saved payment methods, mobile-money transactions, and provider callbacks |
| `support` | Support tickets and messages |
| `operations` | Admin dashboard, driver reviews, pricing tiers, and surge zones |
| `gosmart_backend` | Django settings and ASGI/WSGI entry points |

Models, serializers, permissions, services, and URL modules live with the feature
that owns them. `api/` is a compatibility and API-aggregation package only;
new feature code belongs in the relevant app.

## Local setup

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Create the PostgreSQL role and database (see PostgreSQL below).
createuser --pwprompt gosmart
createdb --owner=gosmart gosmart
# Set DATABASE_URL in .env to use the password entered above.
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

The API is under `/api/v1/`. Django admin is under `/django-admin/`.
Interactive Swagger documentation is available at `/api/docs/`, and the
OpenAPI schema is at `/api/schema/`. Use the **Authorize** button in Swagger
and enter a JWT access token to try authenticated endpoints. Endpoints are
grouped by app in separate Swagger sections.

### PostgreSQL

The backend uses PostgreSQL when `DATABASE_URL` is a PostgreSQL connection URL.
The example `.env` configures a local database named `gosmart`; create the role
and database using the commands in Local setup, or create them with your
PostgreSQL administration tool. In `backend/.env`, replace the example
password in `DATABASE_URL` with the password you set; its format is
`postgresql://gosmart:<password>@localhost:5432/gosmart`.

The database driver and URL parser are included in `requirements.txt`. If
`DATABASE_URL` is unset, settings retain SQLite as a development fallback. Set
a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and explicit hosts/origins
before deployment.

### Mobile app connection and languages

The app connects to Django through the shared `gosmart/src/services/api.ts`
REST client. Set `EXPO_PUBLIC_API_URL` in `gosmart/.env` to the API root, for
example `http://192.168.1.20:8000/api/v1` when using a physical phone on the
same network. Restart Expo after changing the value. The app sends JWT bearer
tokens for authenticated requests and sends `Accept-Language: rw`, `en`, or
`fr` based on the language selected in Settings. Login/register responses set
the in-memory JWTs and refresh them after a 401 response; call
`clearAuthTokens()` when logging out. Tokens currently live in memory only, so
the app does not retain a signed-in session after it is restarted.

`GET /api/v1/languages/` returns the supported languages and current request
language. Send `Accept-Language` with any API request to select Kinyarwanda,
English, or French; unsupported values fall back to English. Supported API
error messages are translated and responses include a `Content-Language`
header. The profile endpoint accepts `preferred_language` to persist a user's
preference when the app is authenticated.

### Screen API map

- Passenger authentication/profile: `/auth/register/`, `/auth/login/`,
  `/auth/me/`, `/profile/`, and `/auth/otp/`
- Passenger ride flow: `/fares/quote/`, `/rides/`, ride cancel/payment intent/
  trip PIN/rating actions, `/payment-methods/`, `/saved-places/`, and
  `/emergency-alerts/`
- Driver flow: `/driver/profile/`, `/driver/preferences/`, `/driver/requests/`,
  `/driver/documents/`, `/driver/earnings/`, and `/driver/cashouts/`
- Support: `/support/tickets/` and ticket messages
- Operations: `/admin/dashboard/`, `/admin/drivers/`, `/admin/pricing/`,
  `/admin/surge-zones/`, and `/admin/support/tickets/`

## Third-party integrations

SMS and mobile-money providers are not guessed or simulated as successful.
Set `SMS_PROVIDER_URL` / `SMS_PROVIDER_API_KEY` and
`MOMO_PROVIDER_URL` / `MOMO_PROVIDER_API_KEY` to provider-compatible endpoints.
`OTP_EXPOSE_IN_DEBUG=true` is a local-development-only option to expose the OTP
in the response. Never enable it outside development.

Provider integrations must be tested against the chosen provider's verified
request, callback-signature, and payout specifications before launch. An
unconfigured mobile-money payment returns an explicit service-unavailable
response; it does not mark a transaction as paid.
