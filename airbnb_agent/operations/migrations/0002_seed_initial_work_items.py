from django.db import migrations
from django.utils import timezone


SEED_ITEMS = [
    {
        "slug": "document-mladis-universe-architecture",
        "title": "Document MLADIS Universe Architecture",
        "list_name": "Architecture tasks",
        "neuron": "pyramid",
        "status": "done",
        "priority": "high",
        "next_action": "Use ADR 0001 as the architecture source of truth.",
        "source_url": "https://github.com/pzg8794/MLADIS/blob/feature/signin-contracts-ci/docs/architecture/0001-mladis-universe-neuron-model.md",
        "sort_order": 10,
    },
    {
        "slug": "document-operations-workboard-gentelella-plan",
        "title": "Document Operations Workboard + Gentelella Plan",
        "list_name": "Architecture tasks",
        "neuron": "operations",
        "status": "done",
        "priority": "high",
        "next_action": "Implement the owner-only MVP behind the MLADIS ops shell.",
        "source_url": "https://github.com/pzg8794/MLADIS/blob/feature/signin-contracts-ci/docs/architecture/0002-operations-workboard-gentelella.md",
        "sort_order": 20,
    },
    {
        "slug": "build-owner-only-operations-workboard",
        "title": "Build owner-only Operations Workboard MVP",
        "list_name": "Product tasks",
        "neuron": "operations",
        "status": "in_progress",
        "priority": "critical",
        "next_action": "Verify owner-only API, completion toggles, local runtime, and CI tests.",
        "source_url": "https://github.com/ColorlibHQ/gentelella",
        "sort_order": 10,
    },
    {
        "slug": "complete-new-york-publication",
        "title": "Complete New York publication requirement",
        "list_name": "Business tasks",
        "neuron": "operations",
        "status": "in_progress",
        "priority": "critical",
        "next_action": "Wait for The Forum reply, track six weeks, collect affidavits, then file Certificate of Publication.",
        "source_url": "https://github.com/pzg8794/MLADIS/blob/feature/signin-contracts-ci/docs/business/publication/publication-completion-checklist.md",
        "sort_order": 10,
    },
    {
        "slug": "open-mladis-business-bank-account",
        "title": "Open MLADIS LLC business checking account",
        "list_name": "Business tasks",
        "neuron": "finance",
        "status": "planned",
        "priority": "high",
        "next_action": "Use the bank packet and private EIN letter during bank onboarding.",
        "source_url": "https://github.com/pzg8794/MLADIS/blob/feature/signin-contracts-ci/docs/business/ein-and-banking/bank-account-opening-packet.md",
        "sort_order": 20,
    },
    {
        "slug": "build-lender-grant-investor-data-room",
        "title": "Build lender, grant, and investor data room",
        "list_name": "Business tasks",
        "neuron": "finance",
        "status": "planned",
        "priority": "high",
        "next_action": "Export Airbnb revenue history, expense history, monthly P&L, forecast, and use-of-funds plan.",
        "source_url": "https://github.com/pzg8794/MLADIS/blob/feature/signin-contracts-ci/docs/business/funding-readiness/data-room-index.md",
        "sort_order": 30,
    },
    {
        "slug": "align-maintenance-with-finance-pyramid",
        "title": "Align maintenance workflow with Finance and Pyramid",
        "list_name": "Product tasks",
        "neuron": "booking",
        "status": "planned",
        "priority": "high",
        "next_action": "Link maintenance costs to Finance expenses and photo/report evidence to Pyramid.",
        "source_url": "https://github.com/pzg8794/MLADIS/blob/feature/signin-contracts-ci/docs/maintenance-mvc-architecture.md",
        "sort_order": 20,
    },
    {
        "slug": "plan-research-neuron-migration",
        "title": "Plan Research neuron migration",
        "list_name": "Architecture tasks",
        "neuron": "research",
        "status": "captured",
        "priority": "medium",
        "next_action": "Create a Research migration plan before moving Quantum MAB, EQUITAS, and AI fairness assets.",
        "source_url": "https://github.com/pzg8794/MLADIS/blob/feature/signin-contracts-ci/docs/roadmap/MLADIS_MASTER_TODO.md",
        "sort_order": 30,
    },
]


def seed_work_items(apps, schema_editor):
    OperationsWorkItem = apps.get_model("operations", "OperationsWorkItem")
    now = timezone.now()
    for item in SEED_ITEMS:
        defaults = dict(item)
        slug = defaults.pop("slug")
        if defaults.get("status") == "done":
            defaults["completed_at"] = now
        OperationsWorkItem.objects.update_or_create(slug=slug, defaults=defaults)


def remove_work_items(apps, schema_editor):
    OperationsWorkItem = apps.get_model("operations", "OperationsWorkItem")
    OperationsWorkItem.objects.filter(slug__in=[item["slug"] for item in SEED_ITEMS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_work_items, remove_work_items),
    ]
