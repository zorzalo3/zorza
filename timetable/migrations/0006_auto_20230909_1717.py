# Generated by Django 2.2.28 on 2023-09-09 17:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0005_auto_20230321_0920'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='reservation',
            unique_together={('period_number', 'room')},
        ),
    ]
