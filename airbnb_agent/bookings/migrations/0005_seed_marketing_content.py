from decimal import Decimal

from django.db import migrations


def img(url):
    return f"{url}?im_w=1200&quality=80&auto=webp"


STAYS = [
    {
        "slug": "mladis-santo-domingo-vacation-home",
        "defaults": {
            "name": "6 Bedrooms Vacation Home & Pool",
            "short_description": "A spacious Santo Domingo stay for groups who want bedrooms, privacy, pool time, and direct host support.",
            "description": "Official Airbnb listing 588632365342578374, mirrored here for direct inquiries and future agent-assisted booking.",
            "marketing_headline": "A larger Santo Domingo home base for families, groups, and longer tropical stays.",
            "marketing_description": "This stay is built for travelers who need room to spread out without losing the comfort of direct host support. Use it as a Santo Domingo base for family visits, celebrations, beach days, local food, and easy coordination before arrival.",
            "location_label": "Santo Domingo, Dominican Republic",
            "image": img("https://a0.muscache.com/im/pictures/miso/Hosting-588632365342578374/original/6fe55920-ce15-4bbc-b560-3ecf159c192d.jpeg"),
            "image_alt": "Airbnb photo for the 6 Bedrooms Vacation Home & Pool in Santo Domingo",
            "airbnb_listing_id": "588632365342578374",
            "airbnb_url": "https://www.airbnb.com/rooms/588632365342578374?guests=1&adults=1&s=66&source=embed_widget",
            "airbnb_rating": Decimal("4.69"),
            "review_count": 26,
            "rating_accuracy": Decimal("4.85"),
            "rating_checkin": Decimal("4.85"),
            "rating_cleanliness": Decimal("4.92"),
            "rating_communication": Decimal("5.00"),
            "rating_location": Decimal("4.23"),
            "rating_value": Decimal("4.92"),
            "bedrooms": 6,
            "beds": 8,
            "bathroom_label": "4 private baths",
        },
        "images": [
            ("Arrival-ready stay", "6fe55920-ce15-4bbc-b560-3ecf159c192d.jpeg"),
            ("Group-friendly living", "d898d590-5c97-4097-92d2-2a2bc65258a5.jpeg"),
            ("Vacation home detail", "df77e983-a750-4e97-b60a-74adb18ed48e.jpeg"),
            ("Room to spread out", "6db428ab-5663-440a-bf2b-6d5cf2b09f71.jpeg"),
            ("Santo Domingo stay", "a3164000-16f9-413b-b86d-50a40359e070.jpeg"),
            ("Pool and comfort", "b69c63d9-fc4e-4d11-a5c9-577128409ced.jpeg"),
        ],
        "hosting": "588632365342578374",
        "themes": [
            ("Communication", "Guests see clear, direct host support as a strength."),
            ("Cleanliness", "The listing reports a strong Airbnb cleanliness score."),
            ("Value", "The stay is positioned for groups who need space."),
            ("Group space", "A larger layout makes it easier to travel together."),
        ],
    },
    {
        "slug": "mladis-three-bedroom-vacation-home",
        "defaults": {
            "name": "3 Bedrooms Vacation Home & Pool G-102",
            "short_description": "A three-bedroom Santo Domingo stay with room for family trips, longer visits, and pool-centered downtime.",
            "description": "Official Airbnb listing 587194328968598250, available for direct inquiries while live availability is connected.",
            "marketing_headline": "A relaxed three-bedroom stay for travelers who want comfort near Santo Domingo.",
            "marketing_description": "This vacation home gives smaller groups a practical base with the same warm MLADIS support. It is a fit for family visits, city plans, and travelers who want to ask questions before booking.",
            "location_label": "Santo Domingo, Dominican Republic",
            "image": img("https://a0.muscache.com/im/pictures/miso/Hosting-587194328968598250/original/0c11621f-bae3-41b1-846f-c50f923b9bd8.jpeg"),
            "image_alt": "Airbnb photo for the 3 Bedrooms Vacation Home & Pool G-102",
            "airbnb_listing_id": "587194328968598250",
            "airbnb_url": "https://www.airbnb.com/rooms/587194328968598250?guests=1&adults=1&s=66&source=embed_widget",
            "airbnb_rating": Decimal("4.88"),
            "review_count": 24,
            "rating_accuracy": Decimal("4.83"),
            "rating_checkin": Decimal("4.96"),
            "rating_cleanliness": Decimal("4.83"),
            "rating_communication": Decimal("5.00"),
            "rating_location": Decimal("4.54"),
            "rating_value": Decimal("4.75"),
            "bedrooms": 3,
            "beds": 4,
            "bathroom_label": "2 private baths",
        },
        "images": [
            ("Pool and home base", "0c11621f-bae3-41b1-846f-c50f923b9bd8.jpeg"),
            ("Three-bedroom comfort", "9b24f453-fc4f-4c1c-8514-f1a628be7f61.jpeg"),
            ("Guest-ready space", "1a7e96a6-6fda-432b-ac47-6dc501a5061c.jpeg"),
            ("Vacation home room", "2d381425-48b6-4464-bd10-52247a3bb64f.jpeg"),
            ("Santo Domingo comfort", "21c8c598-443d-4fb0-b382-6cd6a52a2982.jpeg"),
            ("Travel-ready stay", "05d8ede0-bdd6-45e3-b444-dff87f2b89df.jpeg"),
        ],
        "hosting": "587194328968598250",
        "themes": [
            ("Check-in", "Airbnb reports a high check-in category score."),
            ("Communication", "Guests can rely on direct host communication."),
            ("Family fit", "Three bedrooms make it easier for families to travel together."),
            ("Pool time", "The stay is positioned for vacation downtime."),
        ],
    },
    {
        "slug": "mladis-santo-domingo-guest-home",
        "defaults": {
            "name": "3 Bedrooms Vacation Home & Pool G-101",
            "short_description": "A highly rated three-bedroom home base for Santo Domingo stays, family visits, and island plans.",
            "description": "Official Airbnb listing 582161420407543691, ready for customer questions and quote requests.",
            "marketing_headline": "A trusted three-bedroom stay with the strongest Airbnb review score in the MLADIS collection.",
            "marketing_description": "This stay pairs a comfortable layout with strong guest proof. It gives visitors a dependable Santo Domingo base while MLADIS builds toward a fuller direct booking and concierge experience.",
            "location_label": "Santo Domingo, Dominican Republic",
            "image": img("https://a0.muscache.com/im/pictures/miso/Hosting-582161420407543691/original/c097c0de-d8eb-45da-be8a-644065f20ab8.jpeg"),
            "image_alt": "Airbnb photo for the 3 Bedrooms Vacation Home & Pool G-101",
            "airbnb_listing_id": "582161420407543691",
            "airbnb_url": "https://www.airbnb.com/rooms/582161420407543691?guests=1&adults=1&s=66&source=embed_widget",
            "airbnb_rating": Decimal("4.93"),
            "review_count": 42,
            "rating_accuracy": Decimal("4.95"),
            "rating_checkin": Decimal("4.88"),
            "rating_cleanliness": Decimal("4.98"),
            "rating_communication": Decimal("5.00"),
            "rating_location": Decimal("4.48"),
            "rating_value": Decimal("4.93"),
            "bedrooms": 3,
            "beds": 4,
            "bathroom_label": "2 private baths",
        },
        "images": [
            ("Top-rated stay", "c097c0de-d8eb-45da-be8a-644065f20ab8.jpeg"),
            ("Guest home detail", "b813ecfe-ed2c-43d9-96f7-97a9ef11f75f.jpeg"),
            ("Three-bedroom home", "94d8a020-c81f-4a86-b78d-122d42af6c54.jpeg"),
            ("Vacation-ready space", "d4fac2de-e168-46b5-9074-d26ba8689048.jpeg"),
            ("Pool and comfort", "76cf52a2-094d-483a-af8e-63c3afc9e041.jpeg"),
            ("Santo Domingo base", "b719d867-9ca9-4896-ad0b-e50d822f70f5.jpeg"),
        ],
        "hosting": "582161420407543691",
        "themes": [
            ("Cleanliness", "The listing reports a standout cleanliness category score."),
            ("Communication", "Guests see communication as a clear strength."),
            ("Value", "A strong Airbnb value score supports booking confidence."),
            ("Trusted stay", "The highest review count in the current MLADIS collection."),
        ],
    },
]


CAUSES = [
    {
        "slug": "children-with-cancer",
        "name": "Children with cancer",
        "description": "Support for children and families facing cancer-related needs in the community.",
        "sort_order": 1,
    },
    {
        "slug": "school-support",
        "name": "School support",
        "description": "Help with school supplies, classroom needs, and practical support for students.",
        "sort_order": 2,
    },
    {
        "slug": "community-mission",
        "name": "Community mission",
        "description": "Flexible mission support for local care, family needs, and community projects.",
        "sort_order": 3,
    },
]


def seed_marketing_content(apps, _schema_editor):
    BookableItem = apps.get_model("bookings", "BookableItem")
    StayGalleryImage = apps.get_model("bookings", "StayGalleryImage")
    ReviewTheme = apps.get_model("bookings", "ReviewTheme")
    MissionCause = apps.get_model("bookings", "MissionCause")
    CalendarFeed = apps.get_model("bookings", "CalendarFeed")

    for stay in STAYS:
        item = BookableItem.objects.get(slug=stay["slug"])
        defaults = {
            "category": "stay",
            "starting_price": None,
            "price_unit": "night",
            "max_guests": None,
            "bathrooms": None,
            "is_featured": True,
            "is_active": True,
            **stay["defaults"],
        }
        for field, value in defaults.items():
            setattr(item, field, value)
        item.save()

        StayGalleryImage.objects.filter(item=item).delete()
        ReviewTheme.objects.filter(item=item).delete()

        for order, (caption, filename) in enumerate(stay["images"], start=1):
            StayGalleryImage.objects.create(
                item=item,
                sort_order=order,
                image_url=img(
                    f"https://a0.muscache.com/im/pictures/miso/Hosting-{stay['hosting']}/original/{filename}"
                ),
                alt_text=f"{caption} at {item.name}",
                caption=caption,
            )

        for order, (label, description) in enumerate(stay["themes"], start=1):
            ReviewTheme.objects.create(
                item=item,
                sort_order=order,
                label=label,
                description=description,
            )

        CalendarFeed.objects.update_or_create(
            item=item,
            defaults={
                "google_calendar_name": f"MLADIS - {item.name}",
                "notes": "Manual Airbnb iCal first. Add the Airbnb export URL here, then subscribe/import it into Google Calendar.",
                "is_active": True,
            },
        )

    for cause in CAUSES:
        MissionCause.objects.update_or_create(
            slug=cause["slug"],
            defaults={**cause, "is_active": True},
        )


def unseed_marketing_content(apps, _schema_editor):
    BookableItem = apps.get_model("bookings", "BookableItem")
    StayGalleryImage = apps.get_model("bookings", "StayGalleryImage")
    ReviewTheme = apps.get_model("bookings", "ReviewTheme")
    MissionCause = apps.get_model("bookings", "MissionCause")
    CalendarFeed = apps.get_model("bookings", "CalendarFeed")

    items = BookableItem.objects.filter(slug__in=[stay["slug"] for stay in STAYS])
    StayGalleryImage.objects.filter(item__in=items).delete()
    ReviewTheme.objects.filter(item__in=items).delete()
    CalendarFeed.objects.filter(item__in=items).delete()
    MissionCause.objects.filter(slug__in=[cause["slug"] for cause in CAUSES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_missioncause_bookableitem_image_alt_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_marketing_content, unseed_marketing_content),
    ]
