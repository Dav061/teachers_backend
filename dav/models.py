from decimal import Decimal
from django.db import models 
from datetime import datetime
from django.utils import timezone

# Create your models here.

class Teachers(models.Model):
    title = models.CharField(max_length=50, blank=True, null=True)
    faculty = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True) 
    features = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    available = models.BooleanField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Teachers"
        managed = True
        db_table = 'teachers'
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
    DAY_CHOICES = ( 
        (1, 'Понедельник'), 
        (2, 'Вторник'), 
        (3, 'Среда'), 
        (4, 'Четверг'), 
        (5, 'Пятница'), 
    ) 
    AUDIT_CHOICES = ( 
        (1, '111'), 
        (2, '222'), 
        (3, '333'), 
        (4, '444'), 
        (5, '555'), 
    )
    TIME_CHOICES = ( 
        (1, '8-30'), 
        (2, '10-00'), 
        (3, '12-00'), 
        (4, '14-00'), 
        (5, '18-00'), 
    ) 
    status = models.CharField(choices=STATUS_CHOICES,default=1,max_length=50) 

    day_lesson = models.CharField(choices=DAY_CHOICES,default=1,max_length=20)
    time_lesson = models.CharField(choices=TIME_CHOICES,default=1,max_length=20)
    audit_lesson = models.CharField(choices=AUDIT_CHOICES,default=1,max_length=20)

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


class Applicationsteachers(models.Model):
    application = models.ForeignKey(Applications, on_delete=models.CASCADE, blank=True, null=True) 
    teacher = models.ForeignKey(Teachers, on_delete=models.CASCADE, blank=True, null=True) 

    class Meta:
        verbose_name_plural = "Applicationsteachers"
        managed = True
        db_table = 'applicationsteachers'
        unique_together = (('application', 'teacher'),)