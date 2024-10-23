from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser , BaseUserManager, PermissionsMixin
from django.db import transaction
from datetime import datetime
# Create your models here.

from .utils import schedule_alarm


class UserbungryManager(BaseUserManager):
    def create_user(self,b_id,password =None , **extra_fields):
        if not b_id:
            raise ValueError('The b_id field must be set')
        user = self.model(b_id =b_id , **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self,b_id,password=None,**extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser',True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(b_id,password, **extra_fields)


class Group(models.Model):
    group_code = models.CharField(max_length=70 , unique= True)
    group_name = models.CharField(max_length=70)

    def __str__(self):
        return self.group_name



class Userbungry(AbstractBaseUser,PermissionsMixin):
    b_id = models.CharField(max_length=70)
    nickname = models.CharField(max_length=70)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # 웹소켓과, 푸시알림 처리 병행을 위해, 컬럼 추가
    web_active = models.BooleanField(default=False)
    # fcm_token 을 저장하기 위한, 컬럼 추가
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    # ios or android 처리
    device_type = models.CharField(max_length=70 , null = True)
    # group 관리
    group = models.ForeignKey(Group,on_delete=models.SET_NULL, null=True , blank=True )


    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = [ ]

    objects = UserbungryManager()

    def __str__(self):
        return self.b_id




class Alarm(models.Model):
    id_user = models.ForeignKey(Userbungry , on_delete=models.CASCADE)
    date = models.DateTimeField()
    title = models.CharField(max_length = 150)
    detail = models.CharField(max_length=1000)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        transaction.on_commit(lambda:(
            print(f"트랜잭션 커밋 시점: {self.id} at {datetime.now()}"),
            schedule_alarm(self)
        ))

    def __str__(self):
        return self.date