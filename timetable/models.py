from django.db import models
from django.utils.translation import gettext as _

class Class(models.Model):
    name = models.CharField(max_length=20)

class Group(models.Model):
    name = models.CharField(max_length=20)
    classes = models.ManyToManyField(Class)

class Subject(models.Model):
    name = models.CharField(max_length=20)

class Teacher(models.Model):
    name = models.CharField(max_length=100)
    initials = models.CharField(max_length=3)

class Room(models.Model):
    full_name = models.CharField(max_length=20)
    short_name = models.CharField(max_length=5)

DAY_OF_THE_WEEK = (
    ('1', _('Monday')),
    ('2', _('Tuesday')),
    ('3', _('Wednesday')),
    ('4', _('Thursday')),
    ('5', _('Friday')),
    ('6', _('Saturday')),
    ('7', _('Sunday')),
)


class Period(models.Model):
    weekday = models.CharField(max_length=2, choices=DAY_OF_THE_WEEK)
    begin_time = models.TimeField()
    end_time = models.TimeField()
    def __str__(self): # Display time range
        pass

class Lesson(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
