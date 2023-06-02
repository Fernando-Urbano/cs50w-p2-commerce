# Generated by Django 4.1.7 on 2023-06-02 14:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("auctions", "0009_auction_closed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auction",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="auctions",
                to="auctions.category",
            ),
        ),
    ]