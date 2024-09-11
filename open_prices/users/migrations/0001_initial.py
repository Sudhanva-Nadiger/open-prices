# Generated by Django 5.1 on 2024-09-03 16:21

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("user_id", models.CharField(primary_key=True, serialize=False)),
                ("is_moderator", models.BooleanField(default=False)),
                (
                    "price_count",
                    models.PositiveIntegerField(blank=True, default=0, null=True),
                ),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "verbose_name": "User",
                "verbose_name_plural": "Users",
                "db_table": "users",
            },
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("token", models.CharField(unique=True)),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_used", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="sessions",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Session",
                "verbose_name_plural": "Sessions",
                "db_table": "sessions",
            },
        ),
    ]