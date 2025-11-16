from django.db import models

class vehicle(models.Model):
    COLOR_CHOICES = (
        ('1', 'ROJO'),
        ('2', 'AZUL'),
        ('3', 'VERDE'),
    )

    placa = models.CharField(max_length=6)
    marca = models.CharField(max_length=50)
    color_vehiculo = models.CharField(max_length=1, choices=COLOR_CHOICES)
    modelo = models.IntegerField()

    def __str__(self):
        return f"{self.placa} - {self.marca}"
