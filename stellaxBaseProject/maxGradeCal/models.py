from django.db import models

# Create your models here.


class GradeCal(models.Model):
    
    max_points = models.FloatField()
    option = models.FloatField()
    
    