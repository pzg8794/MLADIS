from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0025_maintenance_ai_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookinginquiry",
            name="accepted_damage_terms_version",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="bookinginquiry",
            name="accepted_property_rules_version",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="bookinginquiry",
            name="damage_terms_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="bookinginquiry",
            name="property_rules_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="property_rules_title",
            field=models.CharField(default="Property Rules", max_length=160),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="property_rules_version",
            field=models.CharField(default="2026-06-15", max_length=32),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="property_rules_body",
            field=models.TextField(
                blank=True,
                default=(
                    "Registered guests only. The reservation guest count must be accurate before arrival.\n\n"
                    "Check-in is 3:00 PM and check-out is 12:00 PM unless MLADIS confirms another time in writing.\n\n"
                    "No parties, events, disruptive noise, or behavior that disturbs neighbors, staff, guards, or other residents.\n\n"
                    "No smoking inside the apartment or indoor shared areas.\n\n"
                    "Keep doors, windows, balcony doors, and access points secured when leaving the apartment.\n\n"
                    "Guests are responsible for ordinary care of furniture, keys, access devices, appliances, linens, towels, kitchen items, electronics, and shared amenities.\n\n"
                    "Any violation that causes fines, damage, cleaning costs, missing items, access replacement costs, vendor charges, or other loss may be charged according to the Damage Deposit Hold Terms."
                ),
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="damage_terms_title",
            field=models.CharField(default="Damage Deposit Hold Terms", max_length=160),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="damage_terms_version",
            field=models.CharField(default="2026-06-15", max_length=32),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="damage_terms_body",
            field=models.TextField(
                blank=True,
                default=(
                    "The refundable damage deposit is an authorization hold used to protect MLADIS, the property owner, and future guests from property damage, missing items, excessive cleaning, rule violations, residential fines, access-device replacement, and other costs caused during a reservation.\n\n"
                    "The hold is not automatically captured. MLADIS may capture all or part of the hold only when there is a documented reason connected to the stay, including property damage, missing items, broken appliances or furniture, smoke or odor remediation, excessive cleaning, lost keys or access devices, unauthorized guests, unauthorized parties, amenity misuse, parking or building fines, or other violations of the property rules.\n\n"
                    "If damage or a rule violation exceeds the deposit amount, MLADIS may seek the remaining balance through invoice, payment request, platform claim, legal claim, or another lawful recovery method.\n\n"
                    "If no issue is documented, the hold should be released according to the payment processor and card issuer timeline."
                ),
            ),
        ),
    ]
