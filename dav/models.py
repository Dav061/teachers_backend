from django.db import models
from django.utils import timezone
from django.contrib.auth.models import UserManager,User, PermissionsMixin, AbstractBaseUser


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
    

class NewUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, email, password="1234", **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class Users(AbstractBaseUser, PermissionsMixin):
    email = models.CharField(max_length=500,unique=True) 
    password = models.CharField(max_length=400, blank=True, null=True) 
    is_moderator = models.BooleanField(blank=True, null=True) 

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'

    objects =  NewUserManager()

    class Meta: 
        verbose_name_plural = "Users" 
        managed = True

    def __str__(self): 
        return self.email
    

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

    TIME_CHOICES = ( 
        (1, '8-30'), 
        (2, '10-00'), 
        (3, '12-00'), 
        (4, '14-00'), 
        (5, '18-00'), 
    )

    audience = models.CharField(default="306э", max_length=20, null=True)

    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    day_lesson = models.IntegerField(choices=DAY_CHOICES,default=1, null=True)
    time_lesson = models.IntegerField(choices=TIME_CHOICES,default=1, null=True)

    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)    
    formed_at = models.DateTimeField(blank=True, null=True) 
    completed_at = models.DateTimeField(blank=True, null=True)

    moderator = models.ForeignKey(Users, on_delete=models.CASCADE, blank=True, null=True)
    customer = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='applications_customer_set', blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Applications"    
        managed = True 
        db_table = 'applications'

    def __str__(self):
        return f"Занятие №{self.pk}"


class Applicationsoptions(models.Model):
    application = models.ForeignKey(Applications, on_delete=models.CASCADE, blank=True, null=True) 
    option = models.ForeignKey(Options, on_delete=models.CASCADE, blank=True, null=True) 

    class Meta:
        verbose_name_plural = "Applicationsoptions"
        managed = True
        db_table = 'applicationsoptions'