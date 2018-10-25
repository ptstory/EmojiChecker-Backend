from datetime import datetime, timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from api.sms import SMS

def get_expiration():
    return datetime.now() + timedelta(minutes=10)

class User(AbstractUser):
    phone_number = PhoneNumberField(unique=True, help_text="Use E164 Format")
    birth_date = models.DateField()
    is_current_subject = models.BooleanField(default=True)
    REQUIRED_FIELDS = ['birth_date', 'phone_number', 'first_name', 'last_name', 'email']

    def send_message(self, sms_obj):
        return sms_obj.send(self.phone_number)


class Emoji(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    description = models.TextField(null=True, blank=True)
    emoji = models.CharField(null=True, blank=True, max_length=2, help_text='The actual emoji 💩')

    def __str__(self):
        if self.emoji is not None:
            return self.emoji + ' - ' + self.name
        return self.name


class Message(models.Model):
    name = models.CharField(max_length=20)
    description = models.TextField(null=True)
    created = models.DateField(auto_now_add=True)
    text = models.CharField(max_length=140)

    def __str__(self):
        return self.name


class Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.ForeignKey(Emoji, on_delete=models.DO_NOTHING)
    ts = models.DateTimeField(auto_now_add=True)


class ScheduleManager(models.Manager):
    def check_schedule(self):
        now = datetime.now()
        return self.model.objects.filter(sent=False).filter(send_at__lte=now)


class Schedule(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    send_at = models.DateTimeField(help_text="Use ISO 8601 format. All times are UTC.")
    users = models.ManyToManyField(User)
    sent = models.BooleanField(default=False,
                               help_text="Does not indicate success/failure, only whether an attempt was made")
    objects = ScheduleManager()
    expiration = models.DateTimeField(default=get_expiration)

    def send_scheduled_message(self):
        users = self.users.all()
        sms_obj = SMS(message=self.message.text)

        for user in users:
            response = user.send_message(sms_obj)
            if 'MessageID' in response:
                self.sendlog_set.create(success=True, user=user)
            else:
                self.sendlog_set.create(success=False, log_message=response, user=user)

        self.sent = True
        self.save()




class SendLog(models.Model):
    response = models.OneToOneField(Response, on_delete=models.CASCADE, null=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ts = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    log_message = models.TextField(null=True)

    def __str__(self):
        return f'{self.ts} - {self.success} - {self.log_message}'
