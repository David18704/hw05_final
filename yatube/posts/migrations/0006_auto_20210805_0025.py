# Generated by Django 2.2.6 on 2021-08-04 21:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20210804_2353'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='self_following',
        ),
    ]
