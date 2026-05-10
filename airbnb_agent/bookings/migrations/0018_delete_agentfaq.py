from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0017_merge_agentfaq_and_knowledge_sources"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AgentFAQ",
        ),
    ]