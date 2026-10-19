import secrets

from django.contrib.auth.hashers import check_password, make_password


def verify_trip_pin(ride, pin):
    return bool(ride.start_pin_hash and check_password(pin, ride.start_pin_hash))


def issue_trip_pin(ride):
    pin = f"{secrets.randbelow(10000):04d}"
    ride.start_pin_hash = make_password(pin)
    ride.save(update_fields=("start_pin_hash",))
    return pin
