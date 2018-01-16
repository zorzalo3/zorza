from django.contrib import admin
from .models import *

# Register your models here.

class LessonInline(admin.TabularInline):
    model = Lesson

class GroupsInline(admin.TabularInline):
    model = Group.classes.through

class PeriodInline(admin.TabularInline):
    model = Period

class GroupAdmin(admin.ModelAdmin):
    inlines = [LessonInline, GroupsInline]

class ClassAdmin(admin.ModelAdmin):
    inlines = [GroupsInline]

class SubjectAdmin(admin.ModelAdmin):
    inlines = [LessonInline]

class TeacherAdmin(admin.ModelAdmin):
    inlines = [LessonInline]

class RoomAdmin(admin.ModelAdmin):
    inlines = [LessonInline]

class TimesAdmin(admin.ModelAdmin):
    inlines = [PeriodInline]

admin.site.register(Class, ClassAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Times, TimesAdmin)
admin.site.register(Period)
admin.site.register(DayPlan)
admin.site.register(Lesson)
admin.site.register(Substitution)
