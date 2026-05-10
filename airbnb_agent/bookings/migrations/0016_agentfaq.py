from django.db import migrations, models
import django.db.models.deletion


FAQS = [
    {
        "category": "deposit",
        "question": "How does the damage deposit work?",
        "answer": "MLADIS uses a refundable $200 USD damage-deposit authorization hold through Stripe or PayPal. It is not captured unless there is a valid damage claim. After you submit the booking form, the secure deposit-hold step appears.",
        "keywords": "deposit, damage deposit, hold, authorization hold, stripe, paypal, refundable, security deposit, deposito, fianza",
        "priority": 100,
    },
    {
        "category": "booking",
        "question": "How do I book a stay?",
        "answer": "To start a reservation, choose the stay, dates, guest count, name, email, and phone in the booking form. If you have a coupon, add it there too. A MLADIS admin reviews availability and confirms the reservation by email.",
        "keywords": "book, booking, reserve, reservation, reservar, dates, guests, email, phone, coupon",
        "priority": 95,
    },
    {
        "category": "availability",
        "question": "Is availability guaranteed?",
        "answer": "Availability is not guaranteed until a MLADIS admin reviews and confirms your request. Please submit your dates and guest count in the booking form so we can verify the stay and follow up by email.",
        "keywords": "available, availability, dates, calendar, open, disponible, fechas, confirm",
        "priority": 90,
    },
    {
        "category": "pricing",
        "question": "Can I get a discount or coupon?",
        "answer": "If you have a coupon code, enter it in the booking form. Discounts or special pricing must be reviewed by MLADIS and are not guaranteed until confirmed by an admin.",
        "keywords": "discount, coupon, promo, deal, price, pricing, descuento, cupon, oferta",
        "priority": 85,
    },
    {
        "category": "rules",
        "question": "Are parties allowed?",
        "answer": "Parties and rule exceptions are not automatically allowed. Please include your plans in the booking message so MLADIS can review them. The reservation is admin-confirmed and house rules must be followed.",
        "keywords": "party, parties, event, noise, music, guests, regla, fiesta, ruido, smoking, pets",
        "priority": 85,
    },
    {
        "category": "contact",
        "question": "What information do you need from me?",
        "answer": "Please provide the stay you want, check-in and check-out dates, guest count, full name, email, phone number, and any special request. That gives MLADIS what we need to review and confirm the reservation.",
        "keywords": "what do you need, info, information, details, name, email, phone, dates, guests, contacto",
        "priority": 80,
    },
    {
        "category": "payment",
        "question": "Do you accept Stripe or PayPal?",
        "answer": "Yes. The secure refundable damage-deposit authorization can be completed through Stripe Checkout or PayPal after you submit the booking form.",
        "keywords": "stripe, paypal, payment, pay, pagar, tarjeta, card, checkout",
        "priority": 80,
    },
    {
        "category": "agent_scope",
        "question": "Can you help with something unrelated to MLADIS?",
        "answer": "I can help with MLADIS vacation stays, reservations, deposits, amenities, location, rules, and booking next steps. For anything unrelated, please contact the right service provider directly.",
        "keywords": "unrelated, homework, legal, medical, politics, random, not booking, not travel",
        "priority": 60,
    },
]


def seed_faqs(apps, schema_editor):
    AgentFAQ = apps.get_model("bookings", "AgentFAQ")
    for faq in FAQS:
        AgentFAQ.objects.update_or_create(
            question=faq["question"],
            defaults={
                **faq,
                "min_score": "0.55",
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0015_customerfeedback"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgentFAQ",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(blank=True, max_length=80)),
                ("question", models.CharField(max_length=240, unique=True)),
                ("answer", models.TextField()),
                ("keywords", models.CharField(blank=True, help_text="Comma-separated trigger words or phrases.", max_length=600)),
                ("language", models.CharField(default="en", max_length=8)),
                ("min_score", models.DecimalField(decimal_places=2, default="0.55", max_digits=4)),
                ("priority", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("item", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="agent_faqs", to="bookings.bookableitem")),
            ],
            options={
                "ordering": ["-priority", "category", "question"],
                "verbose_name": "agent FAQ",
                "verbose_name_plural": "agent FAQs",
            },
        ),
        migrations.RunPython(seed_faqs, migrations.RunPython.noop),
    ]
