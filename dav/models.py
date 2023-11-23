from decimal import Decimal
from django.db import models 
from datetime import datetime
from django.utils import timezone

# Create your models here.

class Options(models.Model):
    title = models.CharField(max_length=50, blank=True, null=True)
    faculty = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True) 
    features = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    available = models.BooleanField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Options"
        managed = True
        db_table = 'options'
    def __str__(self):
        return self.title
    

class Users(models.Model):
    login = models.CharField(max_length=20, blank=True, null=True)
    password = models.CharField(max_length=20, blank=True, null=True)
    is_moderator = models.BooleanField(blank=True, null=True)
    fio = models.CharField(max_length=50, blank=True, null=True) 

    class Meta: 
        verbose_name_plural = "Users" 
        managed = True
        db_table = 'users'
    def __str__(self): 
        return self.title
    

class Applications(models.Model):
    STATUS_CHOICES = ( 
        (1, 'Черновик'), 
        (2, 'Удален'), 
        (3, 'Сформирован'), 
        (4, 'Завершен'), 
        (5, 'Отклонен'), 
    ) 
    status = models.CharField(choices=STATUS_CHOICES,default=1,max_length=20) 
    day_less = models.DateTimeField(blank=True, null=True)
    time_less = models.DateTimeField(unique=True, blank=True, null=True)
    audit_less = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)    
    formed_at = models.DateTimeField(blank=True, null=True) 
    completed_at = models.DateTimeField(blank=True, null=True) 
    moderator = models.ForeignKey(Users, on_delete=models.CASCADE,blank=True, null=True) 
    customer = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='applications_customer_set', blank=True, null=True) 
    
    class Meta: 
        verbose_name_plural = "Applications" 
        managed = True 
        db_table = 'applications'
    def __str__(self):
        return self.title


class Applicationsoptions(models.Model):
    amount = models.IntegerField(default=1,blank=True, null=True) 
    application = models.ForeignKey(Applications, on_delete=models.CASCADE, blank=True, null=True) 
    option = models.ForeignKey(Options, on_delete=models.CASCADE, blank=True, null=True) 

    class Meta:
        verbose_name_plural = "Applicationsoptions"
        managed = True
        db_table = 'applicationsoptions'
        unique_together = (('application', 'option'),)