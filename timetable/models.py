from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

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
    name = models.CharField(max_length=100)
    initials = models.CharField(max_length=3)

    def __str__(self):
        return self.name

class Room(models.Model):
    name = models.CharField(max_length=40)
    short_name = models.CharField(max_length=3)

    def __str__(self):
        return self.name

class Times(models.Model):
    """A collection of periods (by foreign keys in Period). AKA timetable.

    By default, the timetable with the lowest pk is used.
    """
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name

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
    day = models.DateField(unique=True)
    timetable = models.ForeignKey(Times, on_delete=models.CASCADE, null=True)
    # None if no timetable (eg. lessons cancelled)

    def __str__(self):
        return str(day)

class Lesson(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    # TODO: change period to a number
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=settings.TIMETABLE_WEEKDAYS)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s %s, %s, %s %d %s' % \
            (self.teacher.initials, self.subject.short_name,
             self.room.short_name, self.group.name, _('Lesson'),
             self.period.number, settings.TIMETABLE_WEEKDAYS[self.weekday][1])

class Occasion(models.Model):
    date = models.DateField()
    # TODO: after Times is implemented, maybe use two numbers instead
    # of a Period ForeignKey: begin_period and end_period?
    period = models.ForeignKey(Period, on_delete=models.CASCADE)

    @property
    def weekday(self):
        return self.date.weekday()

    class Meta:
        abstract = True

class Substitution(Occasion):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    # teacher is None <=> lesson is cancelled
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE,
                                null=True, blank=True)
    # room is None <=> room for the substitution is unspecified
    room = models.ForeignKey(Room, on_delete=models.CASCADE,
                             null=True, blank=True)

    def __str__(self):
        return '%s %s %s -> %s %s' % (self.date, self.period, self.group, \
                self.teacher, self.room)

class Absence(Occasion):
    reason = models.CharField(max_length=40, blank=True);
    groups = models.ManyToManyField(Group)

    def __str__(self):
        return '%s %s %s (%s)' % (self.date, self.period, self.groups.all(), \
                self.reason)

class Reservation(Occasion):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE,
            null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    def __str__(self):
        return '%s %s %s %s' % (self.date, self.period, self.room, \
                self.teacher)
