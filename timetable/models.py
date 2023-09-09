from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _
from django.utils.formats import date_format


class Class(models.Model):
    """A collection of groups to which students of a class can belong"""
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'classes'

class Group(models.Model):
    name = models.CharField(max_length=17)
    classes = models.ManyToManyField(Class, blank=True)
    # Link directly to class timetable instead of group timetable
    link_to_class = models.BooleanField(default=False)

    def clean(self):
        if (self.link_to_class == True and self.classes.count() != 1):
            raise ValidationError(_('link_to_class needs exactly one class'))

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

class Schedule(models.Model):
    """A collection of periods (by foreign keys in Period).
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
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    def __str__(self): # Display time range
        return '%d:%.2d–%d:%.2d' % \
            (self.begin_time.hour, self.begin_time.minute, \
             self.end_time.hour,   self.end_time.minute)

    def clean(self):
        # Ensure Period numbers of non-default Schedule are a subset of Period
        # numbers of the default Schedule
        if self.schedule.is_default:
            return
        qs = Period.objects.filter(number=self.number,
                                   schedule__is_default=True)
        if not qs.exists():
            raise ValidationError("Period numbers must be a subset of default\
                schedule's period numbers")

    class Meta:
        unique_together = (('number', 'schedule'),)
        ordering = ['schedule', 'number']

class DayPlan(models.Model):
    """A DayPlan says which schedule (or none) to use on a given day"""
    date = models.DateField(unique=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE,
                                  null=True, blank=True)
    # None if no timetable (eg. lessons cancelled)

    def __str__(self):
        return str(self.date)

    @property
    def is_today(self):
        return date.today() == self.date

    @property
    def display_schedule(self):
        return str(self.schedule) if self.schedule else _('cancelled')


    class Meta:
        ordering = ['date']

class Lesson(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    period = models.IntegerField()
    weekday = models.IntegerField(choices=settings.TIMETABLE_WEEKDAYS)
    room = models.ForeignKey(Room, on_delete=models.DO_NOTHING, blank=True, null=True, default=None)

    def __str__(self):
        return '%s %s %s, %s, %s %d %s' % \
            (self.teacher.initials, self.subject.short_name,
             self.room.short_name, self.group.name, _('Lesson'),
             self.period, settings.TIMETABLE_WEEKDAYS[self.weekday][1])

class Occasion(models.Model):
    date = models.DateField()
    period_number = models.IntegerField()

    @property
    def weekday(self):
        return self.date.weekday()

    @property
    def period_str(self):
        from .utils import get_period_str
        return get_period_str(self.period_number, self.date)

    class Meta:
        abstract = True

class Substitution(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    substitute = models.ForeignKey(Teacher, on_delete=models.CASCADE,
            null=True, blank=True, related_name='substitutions')
    date = models.DateField()
    # date is redundant with lesson.weekday, but that makes things easier.

    @property
    def display_substitute(self):
        return self.substitute.full_name if self.substitute else _('cancelled')

    def __str__(self):
        """We must use hasattr, because self.lesson has null=False and
        self.lesson, before initial saving, can be unassigned."""
        period =  None
        teacher_absent =  None
        if hasattr(self,'lesson'):
            period = self.lesson.period
            teacher_absent = self.lesson.teacher.full_name
        return '%s %s %s -> %s' % (self.date, period, teacher_absent, self.display_substitute)

class Absence(Occasion):
    reason = models.CharField(max_length=40, blank=True);
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    @property
    def lesson(self):
        return Lesson.objects.get(
            period=self.period_number, weekday=self.weekday, group=self.group)

    @property
    def room(self):
        query = Lesson.objects.select_related('room') \
            .get(period=self.period_number, weekday=self.weekday, group=self.group)
        return query.room

    def __str__(self):
        return '%s %s %s (%s)' % (self.date, self.period_number, self.group, \
                self.reason)

class Reservation(Occasion):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE,
            null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    @property
    def display_teacher(self):
        return self.teacher.full_name if self.teacher else '-'

    def __str__(self):
        return '%s %s %s %s' % (self.date, self.period_number, self.room, \
                self.teacher)

    class Meta:
        unique_together = ('period_number', 'room')
