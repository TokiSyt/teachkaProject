from django.db import models

# Create your models here.


class GradeCalculator(models.Model):
    
    max_points = models.FloatField()
    option = models.FloatField()
    
    