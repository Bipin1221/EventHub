# Generated by Django 4.2.18 on 2025-01-31 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_events_category_alter_events_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='events',
            name='category',
            field=models.ManyToManyField(blank=True, to='core.category'),
        ),
    ]
