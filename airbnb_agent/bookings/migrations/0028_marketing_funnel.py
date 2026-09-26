from django.db import migrations, models


def connect_physical_units(apps, schema_editor):
    BookableItem = apps.get_model("bookings", "BookableItem")
    combined = BookableItem.objects.filter(slug="mladis-santo-domingo-vacation-home").first()
    g102 = BookableItem.objects.filter(slug="mladis-three-bedroom-vacation-home").first()
    g101 = BookableItem.objects.filter(slug="mladis-santo-domingo-guest-home").first()
    if combined and g101 and g102:
        combined.physical_components.set([g101, g102])

    safe_copy = {
        "mladis-santo-domingo-vacation-home": {
            "max_guests": (None, 14),
            "short_description": (
                "A spacious Santo Domingo stay for groups who want bedrooms, privacy, pool time, and direct host support.",
                "A six-bedroom stay for families, groups, and longer visits in Santo Domingo Norte.",
            ),
            "marketing_headline": (
                "A larger Santo Domingo home base for families, groups, and longer tropical stays.",
                "A larger Santo Domingo Norte home base for families, groups, and longer visits.",
            ),
            "marketing_description": (
                "This stay is built for travelers who need room to spread out without losing the comfort of direct host support. Use it as a Santo Domingo base for family visits, celebrations, beach days, local food, and easy coordination before arrival.",
                "A six-bedroom home base for family visits, group travel, and longer stays in Santo Domingo Norte. Send your dates and guest count to request availability and a complete quote.",
            ),
        },
        "mladis-three-bedroom-vacation-home": {
            "max_guests": (None, 7),
            "short_description": (
                "A three-bedroom Santo Domingo stay with room for family trips, longer visits, and pool-centered downtime.",
                "A three-bedroom stay for family trips and longer visits in Santo Domingo Norte.",
            ),
            "marketing_headline": (
                "A relaxed three-bedroom stay for travelers who want comfort near Santo Domingo.",
                "A three-bedroom stay for family visits and longer trips.",
            ),
            "marketing_description": (
                "This vacation home gives smaller groups a practical base with the same warm MLADIS support. It is a fit for family visits, city plans, and travelers who want to ask questions before booking.",
                "A three-bedroom home base for family visits, city plans, and longer stays in Santo Domingo Norte. Send your dates and guest count to request availability and a complete quote.",
            ),
        },
        "mladis-santo-domingo-guest-home": {
            "max_guests": (None, 7),
            "short_description": (
                "A highly rated three-bedroom home base for Santo Domingo stays, family visits, and island plans.",
                "A three-bedroom stay for Santo Domingo Norte visits and family trips.",
            ),
            "marketing_headline": (
                "A trusted three-bedroom stay with the strongest Airbnb review score in the MLADIS collection.",
                "A three-bedroom stay for family visits in Santo Domingo Norte.",
            ),
            "marketing_description": (
                "This stay pairs a comfortable layout with strong guest proof. It gives visitors a dependable Santo Domingo base while MLADIS builds toward a fuller direct booking and concierge experience.",
                "A three-bedroom home base for family visits and Santo Domingo Norte plans. Send your dates and guest count to request availability and a complete quote.",
            ),
        },
    }
    for slug, updates in safe_copy.items():
        item = BookableItem.objects.filter(slug=slug).first()
        if not item:
            continue
        changed = []
        if item.location_label == "Santo Domingo, Dominican Republic":
            item.location_label = "Santo Domingo Norte, Dominican Republic"
            changed.append("location_label")
        for field, (old_value, new_value) in updates.items():
            if field == "max_guests":
                if item.max_guests is None:
                    item.max_guests = new_value
                    changed.append(field)
                continue
            if getattr(item, field) == old_value:
                setattr(item, field, new_value)
                changed.append(field)
        if changed:
            item.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0027_bookinginquiry_payment_confirmation_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookableitem",
            name="physical_components",
            field=models.ManyToManyField(blank=True, related_name="combined_offers", to="bookings.bookableitem"),
        ),
        migrations.AddField(
            model_name="bookinginquiry",
            name="marketing_attribution",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="pagevisit",
            name="event_id",
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="pagevisit",
            name="event_name",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="pagevisit",
            name="anonymous_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="pagevisit",
            name="campaign_attribution",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(connect_physical_units, migrations.RunPython.noop),
    ]
