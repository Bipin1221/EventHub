# Generated by Django 4.2.19 on 2025-02-14 07:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_eventimage_image'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='rating',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='rating',
            name='event',
        ),
        migrations.RemoveField(
            model_name='rating',
            name='user',
        ),
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(editable=False, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='events',
            name='slug',
            field=models.SlugField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(choices=[('Conferences', 'Conferences'), ('Trade Shows', 'Trade Shows'), ('Networking', 'Networking'), ('WorkShops', 'WorkShops'), ('Product Launch', 'Product Launch'), ('Charity', 'Charity'), ('Music', 'Music'), ('Concert', 'Concert'), ('Performing & Visual Arts', 'Performing & Visual Arts'), ('Food & Drink', 'Food & Drink'), ('Party', 'Party'), ('Sports & Fitness', 'Sports & Fitness'), ('Technology', 'Technology'), ('Digital', 'Digital')], max_length=255, unique=True),
        ),
        migrations.DeleteModel(
            name='Comment',
        ),
        migrations.DeleteModel(
            name='Rating',
        ),
    ]
