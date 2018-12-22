from django.contrib import admin
from .models import *

# Register your models here.

class LessonInline(admin.TabularInline):
    model = Lesson

class GroupsInline(admin.TabularInline):
    model = Group.classes.through

class PeriodInline(admin.TabularInline):
    model = Period

def set_link_to_class(modeladmin, request, queryset):
    queryset.update(link_to_class=True)
set_link_to_class.short_description = "Set 'link to class'"

class GroupAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    actions = [set_link_to_class]

class ClassAdmin(admin.ModelAdmin):
    inlines = [GroupsInline]

class SubjectAdmin(admin.ModelAdmin):
    inlines = [LessonInline]

class TeacherAdmin(admin.ModelAdmin):
    inlines = [LessonInline]

class RoomAdmin(admin.ModelAdmin):
    inlines = [LessonInline]

class ScheduleAdmin(admin.ModelAdmin):
    inlines = [PeriodInline]

admin.site.register(Class, ClassAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(DayPlan)
admin.site.register(Lesson)
admin.site.register(Substitution)
admin.site.register(Absence)
admin.site.register(Reservation)
