from datetime import date

from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _
from django.utils.formats import date_format


class Class(models.Model):
    """A collection of groups to which students of a class can belong"""
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=15)
    classes = models.ManyToManyField(Class, blank=True)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=40)
    short_name = models.CharField(max_length=15)

    def __str__(self):
        return self.name

class Teacher(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    initials = models.CharField(max_length=3)

    @property
    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def __str__(self):
        return '%s %s' % (self.last_name, self.first_name)
        # Reverse name order for better default ordering in lists

    class Meta:
        ordering = ['last_name', 'first_name']

class Room(models.Model):
    name = models.CharField(max_length=40)
    short_name = models.CharField(max_length=3)

    def __str__(self):
        return self.name

class Times(models.Model):
    """A collection of periods (by foreign keys in Period). AKA timetable.
    Only one object has is_default == True. It will be shown on the timetable
    by default.
    """

    name = models.CharField(max_length=40)
    is_default = models.NullBooleanField(default=None, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default is False:
            self.is_default = None
        super().save(*args, **kwargs)

class Period(models.Model):
    number = models.PositiveIntegerField()
    begin_time = models.TimeField()
    end_time = models.TimeField()
    timetable = models.ForeignKey(Times, on_delete=models.CASCADE)

    def __str__(self): # Display time range
        return '%d:%.2d–%d:%.2d' % \
            (self.begin_time.hour, self.begin_time.minute, \
             self.end_time.hour,   self.end_time.minute)

    class Meta:
        unique_together = (('number', 'timetable'),)
        ordering = ['timetable', 'number']

class DayPlan(models.Model):
    """A DayPlan says which timetable (or none) to use on a given day"""
    date = models.DateField(unique=True)
    timetable = models.ForeignKey(Times, on_delete=models.CASCADE,
                                  null=True, blank=True)
    # None if no timetable (eg. lessons cancelled)

    def __str__(self):
        return str(self.date)

    @property
    def is_today(self):
        return date.today() == self.date

class Lesson(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    period = models.IntegerField()
    weekday = models.IntegerField(choices=settings.TIMETABLE_WEEKDAYS)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s %s, %s, %s %d %s' % \
            (self.teacher.initials, self.subject.short_name,
             self.room.short_name, self.group.name, _('Lesson'),
             self.period, settings.TIMETABLE_WEEKDAYS[self.weekday][1])

class Occasion(models.Model):
    date = models.DateField()
    # TODO: after Times is implemented, maybe use two numbers instead
    # of a Period ForeignKey: begin_period and end_period?
    period = models.IntegerField()

    @property
    def weekday(self):
        return self.date.weekday()

    @property
    def period_str(self):
        from .utils import get_period_str
        return get_period_str(self.period, self.date)

    class Meta:
        abstract = True

class Substitution(Occasion):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, \
            related_name='absences')
    # substitute is None <=> lesson is cancelled
    substitute = models.ForeignKey(Teacher, on_delete=models.CASCADE,
            null=True, blank=True, related_name='substitutions')

    @property
    def display_substitute(self):
        return self.substitute.full_name if self.substitute else _('cancelled')

    def __str__(self):
        return '%s %s %s -> %s %s' % (self.date, self.period, self.teacher, \
                self.display_substitute)

class Absence(Occasion):
    reason = models.CharField(max_length=40, blank=True);
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s %s (%s)' % (self.date, self.period, self.group, \
                self.reason)

class Reservation(Occasion):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE,
            null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    @property
    def display_teacher(self):
        return self.teacher.full_name if self.teacher else '-'

    def __str__(self):
        return '%s %s %s %s' % (self.date, self.period, self.room, \
                self.teacher)
