from django.db import migrations


RULES = [
    ("No parties or events", "Keep the stay peaceful for the residential community and nearby neighbors."),
    ("No smoking indoors", "Smoking is not allowed inside the apartment or shared indoor areas."),
    ("Registered guests only", "Guest count must match the reservation unless MLADIS approves a change."),
    ("Respect quiet hours", "Keep noise reasonable, especially late at night and in common areas."),
    ("Protect keys and smart locks", "Report lock, key, or access issues immediately so the host can help."),
]


HIGHLIGHTS = {
    "mladis-santo-domingo-vacation-home": [
        ("Clear communication", "Guests respond well to direct host support before and during the stay."),
        ("Clean group space", "Airbnb public scores point to cleanliness as a confidence builder."),
        ("Strong value for groups", "The larger layout helps families and groups stay together comfortably."),
    ],
    "mladis-three-bedroom-vacation-home": [
        ("Smooth check-in", "Public Airbnb scoring highlights check-in as a strength for this stay."),
        ("Helpful host support", "Communication is one of the strongest public review signals."),
        ("Family-friendly fit", "Three bedrooms make it easier for families and smaller groups to settle in."),
    ],
    "mladis-santo-domingo-guest-home": [
        ("Top cleanliness signal", "This stay carries one of the strongest cleanliness scores in the MLADIS set."),
        ("Trusted communication", "Public review scoring shows communication as a consistent strength."),
        ("High guest proof", "The review count and rating make this a strong confidence pick."),
    ],
}


EXTRA_BILLS = [
    ("Extra cleaning", "Additional cleaning after excessive dirt, trash, or misuse.", 7500),
    ("Broken or missing item", "Replacement or repair for a damaged or missing item.", 5000),
    ("Penalty or rule violation", "Penalty for a confirmed rule violation.", 10000),
    ("Smart lock or key replacement", "Replacement or repair for keys, smart locks, or access devices.", 20000),
]


CONTENT_BLOCKS = [
    (
        "santo-domingo-norte-location",
        "Santo Domingo Norte base",
        "MLADIS stays are positioned around Colinas del Arroyo II, Los Guaricanos, and the Jacobo Majluta corridor.",
        "https://upload.wikimedia.org/wikipedia/commons/e/e3/SantoDomingoedit.JPG",
    ),
    (
        "juan-dolio-day-trip",
        "Juan Dolio day trips",
        "Beach days east of Santo Domingo can add more island energy to a city-centered stay.",
        "https://upload.wikimedia.org/wikipedia/commons/6/62/Juan_Dolio_Beach_1.jpg",
    ),
]


def seed_platform(apps, _schema_editor):
    CancellationPolicy = apps.get_model("bookings", "CancellationPolicy")
    ExtraBillTemplate = apps.get_model("bookings", "ExtraBillTemplate")
    SiteSettings = apps.get_model("bookings", "SiteSettings")
    SiteContentBlock = apps.get_model("bookings", "SiteContentBlock")
    BookableItem = apps.get_model("bookings", "BookableItem")
    HouseRule = apps.get_model("bookings", "HouseRule")
    GuestReviewHighlight = apps.get_model("bookings", "GuestReviewHighlight")
    Coupon = apps.get_model("bookings", "Coupon")

    CancellationPolicy.objects.update_or_create(
        slug="standard-24-hour",
        defaults={
            "name": "Standard 24-hour cancellation",
            "description": "Guests may cancel up to 24 hours before the reservation start date.",
            "allow_guest_cancellation": True,
            "hours_before_check_in": 24,
            "is_default": True,
            "is_active": True,
        },
    )

    Coupon.objects.update_or_create(
        code="WELCOME25",
        defaults={
            "description": "Starter fixed discount for direct MLADIS reservation tests.",
            "discount_type": "fixed",
            "amount_cents": 2500,
            "percent_off": "0.00",
            "currency": "usd",
            "is_active": True,
        },
    )

    SiteSettings.objects.update_or_create(
        pk=1,
        defaults={
            "site_name": "MLADIS LLC",
            "contact_email": "garciapiterz@gmail.com",
            "public_address_label": "Santo Domingo Norte, Dominican Republic",
        },
    )

    for order, (name, description, amount_cents) in enumerate(EXTRA_BILLS, start=1):
        ExtraBillTemplate.objects.update_or_create(
            slug=name.lower().replace(" ", "-"),
            defaults={
                "name": name,
                "description": description,
                "default_amount_cents": amount_cents,
                "currency": "usd",
                "is_active": True,
                "sort_order": order,
            },
        )

    for order, (key, title, body, image_url) in enumerate(CONTENT_BLOCKS, start=1):
        SiteContentBlock.objects.update_or_create(
            key=key,
            defaults={
                "title": title,
                "body": body,
                "image_url": image_url,
                "is_active": True,
                "sort_order": order,
            },
        )

    for item in BookableItem.objects.filter(category="stay"):
        HouseRule.objects.filter(item=item).delete()
        for order, (title, description) in enumerate(RULES, start=1):
            HouseRule.objects.create(
                item=item,
                title=title,
                description=description,
                source_label="Airbnb / MLADIS house rules",
                source_url=item.airbnb_url,
                is_active=True,
                sort_order=order,
            )

        GuestReviewHighlight.objects.filter(item=item).delete()
        for order, (title, body) in enumerate(HIGHLIGHTS.get(item.slug, []), start=1):
            GuestReviewHighlight.objects.create(
                item=item,
                title=title,
                body=body,
                source_label="Airbnb public review signal",
                source_url=item.airbnb_url,
                is_paraphrased=True,
                sort_order=order,
            )


def unseed_platform(apps, _schema_editor):
    CancellationPolicy = apps.get_model("bookings", "CancellationPolicy")
    ExtraBillTemplate = apps.get_model("bookings", "ExtraBillTemplate")
    SiteContentBlock = apps.get_model("bookings", "SiteContentBlock")
    HouseRule = apps.get_model("bookings", "HouseRule")
    GuestReviewHighlight = apps.get_model("bookings", "GuestReviewHighlight")
    Coupon = apps.get_model("bookings", "Coupon")

    CancellationPolicy.objects.filter(slug="standard-24-hour").delete()
    ExtraBillTemplate.objects.filter(slug__in=[name.lower().replace(" ", "-") for name, _, _ in EXTRA_BILLS]).delete()
    SiteContentBlock.objects.filter(key__in=[key for key, *_ in CONTENT_BLOCKS]).delete()
    Coupon.objects.filter(code="WELCOME25").delete()
    HouseRule.objects.filter(source_label="Airbnb / MLADIS house rules").delete()
    GuestReviewHighlight.objects.filter(source_label="Airbnb public review signal").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0006_cancellationpolicy_coupon_extrabilltemplate_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_platform, unseed_platform),
    ]
