from decimal import Decimal

from django.db import migrations


def seed_bookable_items(apps, _schema_editor):
    BookableItem = apps.get_model("bookings", "BookableItem")

    stays = [
        {
            "name": "MLADIS Santo Domingo Vacation Home",
            "slug": "mladis-santo-domingo-vacation-home",
            "short_description": "A large Santo Domingo stay for groups who want space, privacy, and direct host support.",
            "description": "Official Airbnb listing 588632365342578374, mirrored here for direct inquiries and future agent-assisted booking.",
            "location_label": "Santo Domingo, Dominican Republic",
            "image": "",
            "bedrooms": 6,
            "beds": 8,
            "bathroom_label": "4 private baths",
            "airbnb_listing_id": "588632365342578374",
            "airbnb_rating": Decimal("4.69"),
        },
        {
            "name": "MLADIS Three-Bedroom Vacation Home",
            "slug": "mladis-three-bedroom-vacation-home",
            "short_description": "A three-bedroom Santo Domingo stay with room for family trips and longer visits.",
            "description": "Official Airbnb listing 587194328968598250, available for direct inquiries while live availability is connected.",
            "location_label": "Santo Domingo, Dominican Republic",
            "image": "",
            "bedrooms": 3,
            "beds": 4,
            "bathroom_label": "2 private baths",
            "airbnb_listing_id": "587194328968598250",
            "airbnb_rating": Decimal("4.88"),
        },
        {
            "name": "MLADIS Santo Domingo Guest Home",
            "slug": "mladis-santo-domingo-guest-home",
            "short_description": "A highly rated three-bedroom home base for Santo Domingo stays.",
            "description": "Official Airbnb listing 582161420407543691, ready for customer questions and quote requests.",
            "location_label": "Santo Domingo, Dominican Republic",
            "image": "",
            "bedrooms": 3,
            "beds": 4,
            "bathroom_label": "2 private baths",
            "airbnb_listing_id": "582161420407543691",
            "airbnb_rating": Decimal("4.93"),
        },
    ]

    for stay in stays:
        listing_id = stay["airbnb_listing_id"]
        stay.update(
            {
                "category": "stay",
                "airbnb_url": f"https://www.airbnb.com/rooms/{listing_id}?guests=1&adults=1&s=66&source=embed_widget",
                "starting_price": None,
                "price_unit": "night",
                "max_guests": None,
                "bathrooms": None,
                "is_featured": True,
                "is_active": True,
            }
        )
        BookableItem.objects.update_or_create(slug=stay["slug"], defaults=stay)

    BookableItem.objects.update_or_create(
        slug="custom-booking-concierge",
        defaults={
            "name": "Custom Booking Concierge",
            "category": "service",
            "short_description": "Ask for help with add-ons, local coordination, airport pickup, and special trip needs.",
            "description": "This non-stay bookable item keeps the system open for services beyond apartment reservations.",
            "location_label": "Available by request",
            "image": "",
            "starting_price": None,
            "price_unit": "request",
            "max_guests": None,
            "bedrooms": None,
            "beds": None,
            "bathrooms": None,
            "bathroom_label": "",
            "airbnb_listing_id": "",
            "airbnb_url": "",
            "airbnb_rating": None,
            "is_featured": False,
            "is_active": True,
        },
    )


def unseed_bookable_items(apps, _schema_editor):
    BookableItem = apps.get_model("bookings", "BookableItem")
    BookableItem.objects.filter(
        slug__in=[
            "mladis-santo-domingo-vacation-home",
            "mladis-three-bedroom-vacation-home",
            "mladis-santo-domingo-guest-home",
            "custom-booking-concierge",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_bookable_items, unseed_bookable_items),
    ]
