# Generated by Django 2.0.6 on 2018-12-28 11:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dayplan',
            options={'ordering': ['date']},
        ),
    ]
