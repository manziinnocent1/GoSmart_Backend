from django.db import models


class VehicleType(models.TextChoices):
    MOTO = "moto", "Moto"
    CAR = "car", "Car"
    XL = "xl", "XL"
