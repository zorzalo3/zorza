from django.db import models
from django.utils.translation import gettext as _

class Class(models.Model):
    """A collection of groups to which students of a class can belong"""
    name = models.CharField(max_length=20)

class Group(models.Model):
    name = models.CharField(max_length=15)
    classes = models.ManyToManyField(Class, blank=True)

class Subject(models.Model):
    name = models.CharField(max_length=40)
    short_name = models.CharField(max_length=15)

class Teacher(models.Model):
    name = models.CharField(max_length=100)
    initials = models.CharField(max_length=3)

class Room(models.Model):
    full_name = models.CharField(max_length=40)
    short_name = models.CharField(max_length=3)

class Times(models.Model):
    """A collection of periods (by foreign keys in Period). AKA timetable.

    By default, the timetable with the lowest pk is used.
    """
    name = models.CharField(max_length=40)

class Period(models.Model):
    number = models.PositiveIntegerField()
    begin_time = models.TimeField()
    end_time = models.TimeField()
    timetable = models.ForeignKey(Times, on_delete=models.CASCADE)

    def __str__(self): # Display time range
        pass

    class Meta:
        unique_together = (('number', 'timetable'),)
        ordering = ['timetable', 'number']

DAY_OF_THE_WEEK = (
    (0, _('Monday')),
    (1, _('Tuesday')),
    (2, _('Wednesday')),
    (3, _('Thursday')),
    (4, _('Friday')),
    (5, _('Saturday')),
    (6, _('Sunday')),
)

class DayPlan(models.Model):
    """A DayPlan says which timetable (or none) to use on a given day"""
    day = models.DateField(unique=True)
    timetable = models.ForeignKey(Times, on_delete=models.CASCADE, null=True)
    # None if no timetable (eg. lessons cancelled)

class Lesson(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=DAY_OF_THE_WEEK)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
