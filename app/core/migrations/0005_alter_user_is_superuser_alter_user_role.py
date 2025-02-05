# Generated by Django 4.2.18 on 2025-02-01 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_user_is_attendee_user_is_organizer_user_role_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('attendee', 'Attendee'), ('organizer', 'Organizer')], default='attendee', max_length=10),
        ),
    ]
