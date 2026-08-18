import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models as django_models
from django.utils import timezone

from .models import (
    AgentConversation,
    AgentFAQ,
    AirbnbGuestRecord,
    AvailabilityBlock,
    BookableItem,
    BookingInquiry,
    BookingStatus,
    CustomerFeedback,
    CustomerProfile,
    DailyPriceOverride,
    DamageDeposit,
    Donation,
    Invoice,
    MaintenanceEvent,
    PageVisit,
    Promotion,
    ReservationPaymentHold,
)


SCHEMA_VERSION = "1.0"

SENSITIVE_FIELD_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "webhook",
    "session",
)

SIMPLE_OBJECT_LAKE_FOLDERS = (
    "BOOKINGS",
    "CUSTOMERS",
    "BOOKINGAGENTS",
    "TRANSACTIONS",
    "STAYS",
    "MAINTENANCE",
    "WEBSITE",
    "ADMIN",
    "OPERATIONS",
    "EVENTS",
    "INTERACTIONS",
)

MODEL_FOLDER_OVERRIDES = {
    "auth.User": "CUSTOMERS",
    "account.EmailAddress": "CUSTOMERS",
    "socialaccount.SocialAccount": "CUSTOMERS",
    "socialaccount.SocialToken": "CUSTOMERS",
    "socialaccount.SocialApp": "ADMIN",
    "bookings.CustomerProfile": "CUSTOMERS",
    "bookings.AirbnbGuestRecord": "CUSTOMERS",
    "bookings.CustomerFeedback": "CUSTOMERS",
    "bookings.BookingInquiry": "BOOKINGS",
    "bookings.CancellationPolicy": "BOOKINGS",
    "bookings.Coupon": "TRANSACTIONS",
    "bookings.DamageDeposit": "TRANSACTIONS",
    "bookings.ReservationPaymentHold": "TRANSACTIONS",
    "bookings.Donation": "TRANSACTIONS",
    "bookings.Invoice": "TRANSACTIONS",
    "bookings.InvoiceLineItem": "TRANSACTIONS",
    "bookings.ExtraBillTemplate": "TRANSACTIONS",
    "bookings.Promotion": "TRANSACTIONS",
    "bookings.PromotionRecipient": "TRANSACTIONS",
    "bookings.AgentConversation": "BOOKINGAGENTS",
    "bookings.AgentFAQ": "BOOKINGAGENTS",
    "bookings.AgentKnowledgeSource": "BOOKINGAGENTS",
    "bookings.BookableItem": "STAYS",
    "bookings.AvailabilityBlock": "STAYS",
    "bookings.DailyPriceOverride": "STAYS",
    "bookings.CalendarFeed": "STAYS",
    "bookings.GuestReviewHighlight": "STAYS",
    "bookings.HouseRule": "STAYS",
    "bookings.StayGalleryImage": "STAYS",
    "bookings.ReviewTheme": "STAYS",
    "bookings.MaintenanceEvent": "MAINTENANCE",
    "bookings.MaintenancePhoto": "MAINTENANCE",
    "bookings.SiteSettings": "WEBSITE",
    "bookings.SiteContentBlock": "WEBSITE",
    "bookings.AdminAccess": "ADMIN",
    "operations.OperationsWorkItem": "OPERATIONS",
}

COLLECTION_FOLDER_OVERRIDES = {
    "subscriptions": "CUSTOMERS",
    "customer_profiles": "CUSTOMERS",
    "airbnb_guest_records": "CUSTOMERS",
    "customer_feedback": "CUSTOMERS",
    "booking_requests": "BOOKINGS",
    "reservations": "BOOKINGS",
    "agent_conversations": "BOOKINGAGENTS",
    "agent_faq": "BOOKINGAGENTS",
    "damage_deposits": "TRANSACTIONS",
    "reservation_payment_holds": "TRANSACTIONS",
    "donations": "TRANSACTIONS",
    "invoices": "TRANSACTIONS",
    "promotions": "TRANSACTIONS",
    "inventory": "STAYS",
    "availability_blocks": "STAYS",
    "daily_price_overrides": "STAYS",
    "maintenance_events": "MAINTENANCE",
    "page_visits": "EVENTS",
    "object_events": "EVENTS",
    "object_states": "EVENTS",
}


@dataclass(frozen=True)
class DataLakeCollection:
    key: str
    folder: str
    entity_type: str
    description: str
    pii_classification: str


@dataclass(frozen=True)
class DataLakeExportResult:
    export_run_id: str
    root: Path
    schema_only: bool
    redacted: bool
    collection_counts: dict
    manifest_path: Path


class DataLakeJsonEncoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, UUID):
            return str(value)
        return super().default(value)


class DataLakeRecordBuilder:
    def __init__(self, *, redacted=False):
        self.redacted = redacted

    def build(self, *, collection, source_model, entity_id, occurred_at, data, natural_keys=None):
        return {
            "schema_version": SCHEMA_VERSION,
            "collection": collection.key,
            "entity_type": collection.entity_type,
            "record_key": f"{collection.entity_type}:{entity_id}",
            "source_system": "mladis-django",
            "source_model": source_model,
            "source_pk": str(entity_id),
            "pii_classification": "redacted" if self.redacted else collection.pii_classification,
            "occurred_at": self._iso(occurred_at),
            "extracted_at": timezone.now().isoformat(),
            "natural_keys": natural_keys or {},
            "data": self._clean(data),
        }

    def identity(self, value):
        value = (value or "").strip().lower()
        if not value:
            return ""
        if not self.redacted:
            return value
        return hashlib.sha256(f"{settings.SECRET_KEY}:{value}".encode("utf-8")).hexdigest()

    def contact_fields(self, *, email="", phone=""):
        if self.redacted:
            return {
                "email_hash": self.identity(email),
                "phone_hash": self.identity(phone),
            }
        return {
            "email": email or "",
            "phone": phone or "",
        }

    def _iso(self, value):
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    def _clean(self, value):
        if isinstance(value, dict):
            return {key: self._clean(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._clean(item) for item in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, UUID):
            return str(value)
        return value


class SimpleObjectLakeLayout:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()

    def initialize(self):
        self.root.mkdir(parents=True, exist_ok=True)
        for folder in SIMPLE_OBJECT_LAKE_FOLDERS:
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        self._write_root_readme()

    def folder_for_model_label(self, model_label):
        return MODEL_FOLDER_OVERRIDES.get(model_label, "ADMIN")

    def folder_for_collection(self, collection):
        return collection.folder or COLLECTION_FOLDER_OVERRIDES.get(collection.key, "EVENTS")

    def object_path(self, instance):
        folder = self.folder_for_model_label(instance._meta.label)
        return self.root / folder / f"{self._model_key(instance._meta.model_name)}-{instance.pk or 'pending'}.json"

    def history_path_for_instance(self, instance):
        folder = self.folder_for_model_label(instance._meta.label)
        return self.root / folder / "_history.jsonl"

    def event_path_for_instance(self, instance):
        folder = self.folder_for_model_label(instance._meta.label)
        return self.root / folder / "_events.jsonl"

    def collection_path(self, collection):
        folder = self.folder_for_collection(collection)
        return self.root / folder / f"{collection.key}.jsonl"

    def catalog_path(self):
        return self.root / "CATALOG.json"

    def manifest_path(self, export_run_id):
        return self.root / "EXPORTS" / f"export-run-{export_run_id}.json"

    def _model_key(self, model_name):
        return "".join(character if character.isalnum() else "-" for character in model_name.lower()).strip("-")

    def _write_root_readme(self):
        (self.root / "README.md").write_text(
            "\n".join(
                [
                    "# MLADIS Object Lake",
                    "",
                    "Simple Drive-backed JSON object store for MLADIS business objects.",
                    "",
                    "Top-level folders are the contract:",
                    "",
                    "- BOOKINGS: booking requests and reservations.",
                    "- CUSTOMERS: users, customer profiles, Airbnb guests, and feedback.",
                    "- BOOKINGAGENTS: agent conversations, FAQ, and knowledge records.",
                    "- TRANSACTIONS: deposits, payment holds, donations, invoices, coupons, and promotions.",
                    "- STAYS: apartments, availability, pricing, rules, galleries, and calendar feeds.",
                    "- MAINTENANCE: cleaning, repair, maintenance, and photo evidence objects.",
                    "- WEBSITE: site settings and public content objects.",
                    "- ADMIN: admin access and business configuration objects.",
                    "- OPERATIONS: internal workboard tasks and owner-managed operational plans.",
                    "- EVENTS: app/page/workflow events that are not one durable business object.",
                    "- INTERACTIONS: identity-free conversation turns for response-quality learning.",
                    "",
                    "Each business object is stored as one readable JSON file named `<model>-<id>.json`.",
                    "Each folder may also contain `_history.jsonl` for append-only change history.",
                    "",
                    "The Django database remains the transactional source of truth. This object lake is for recovery, audits, analytics, and agent learning.",
                    "Do not store SSNs, EIN letters, raw signatures, bank records, passwords, OAuth secrets, or payment cards here.",
                    "",
                ]
            ),
            encoding="utf-8",
        )


class DataLakeJsonlWriter:
    def write_records(self, path, records):
        path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with path.open("w", encoding="utf-8") as output:
            for record in records:
                output.write(json.dumps(record, cls=DataLakeJsonEncoder, sort_keys=True))
                output.write("\n")
                count += 1
        return count


class DataLakeDriveMirror:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()

    @classmethod
    def from_settings(cls, root):
        return cls(root)

    def copy_path(self, path):
        if not getattr(settings, "MLADIS_DATASTORE_LIVE_SYNC_DRIVE", False):
            return None
        if not shutil.which("rclone"):
            return None
        remote = getattr(settings, "MLADIS_DATASTORE_DRIVE_REMOTE", "")
        folder_id = getattr(settings, "MLADIS_DATASTORE_DRIVE_FOLDER_ID", "")
        if not remote or not folder_id:
            return None

        source = Path(path).expanduser().resolve()
        try:
            relative_path = source.relative_to(self.root).as_posix()
        except ValueError:
            return None

        command = [
            "rclone",
            "copyto",
            str(source),
            f"{remote}:{relative_path}",
            "--drive-root-folder-id",
            folder_id,
            "--drive-pacer-min-sleep",
            getattr(settings, "MLADIS_DATASTORE_DRIVE_PACER_MIN_SLEEP", "3s"),
            "--drive-pacer-burst",
            "1",
            "--tpslimit",
            getattr(settings, "MLADIS_DATASTORE_DRIVE_TPS_LIMIT", "0.25"),
            "--transfers",
            "1",
            "--checkers",
            "1",
            "--retries",
            "3",
            "--low-level-retries",
            "3",
            "--stats-one-line",
        ]
        if getattr(settings, "MLADIS_DATASTORE_LIVE_SYNC_ASYNC", True):
            helper_command = [
                sys.executable,
                "-c",
                (
                    "import subprocess, sys; "
                    "timeout = int(sys.argv[1]); "
                    "cmd = sys.argv[2:]; "
                    "\ntry:\n"
                    "    subprocess.run(cmd, timeout=timeout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
                    "except Exception:\n"
                    "    pass\n"
                ),
                str(getattr(settings, "MLADIS_DATASTORE_DRIVE_COPY_TIMEOUT_SECONDS", 25)),
                *command,
            ]
            try:
                subprocess.Popen(
                    helper_command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            except OSError:
                return None
            return relative_path

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=getattr(settings, "MLADIS_DATASTORE_DRIVE_COPY_TIMEOUT_SECONDS", 25),
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
        return relative_path


class DataLakeObjectEventWriter:
    collection = DataLakeCollection(
        key="object_events",
        folder="EVENTS",
        entity_type="object_event",
        description="Append-only object lifecycle events emitted by live MLADIS workflows.",
        pii_classification="private",
    )

    def __init__(self, root):
        self.layout = SimpleObjectLakeLayout(root)
        self.record_builder = DataLakeRecordBuilder(redacted=False)

    @classmethod
    def from_settings(cls):
        root = (settings.MLADIS_DATASTORE_ROOT or "").strip()
        if not root:
            return NullDataLakeObjectEventWriter()
        return cls(root)

    def write_model_event(self, *, event_name, instance, request=None, data=None):
        self.layout.initialize()
        now = timezone.now()
        event_id = f"{instance._meta.label_lower}:{instance.pk}:{event_name}:{uuid4().hex[:8]}"
        request_data = self._request_data(request)
        record = self.record_builder.build(
            collection=self.collection,
            source_model=instance._meta.label,
            entity_id=event_id,
            occurred_at=now,
            natural_keys={
                "event_name": event_name,
                "source_pk": str(instance.pk or ""),
            },
            data={
                "event_name": event_name,
                "object_model": instance._meta.label,
                "object_pk": instance.pk,
                "request_path": request_data["path"],
                "request_user_id": request_data["user_id"],
                "session_key": request_data["session_key"],
                "data": data or {},
            },
        )
        output_path = self.layout.event_path_for_instance(instance)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, cls=DataLakeJsonEncoder, sort_keys=True) + "\n")
        DataLakeDriveMirror.from_settings(self.layout.root).copy_path(output_path)
        return output_path

    def _request_data(self, request):
        if request is None:
            return {"path": "", "user_id": "", "session_key": ""}
        user = getattr(request, "user", None)
        session = getattr(request, "session", None)
        return {
            "path": getattr(request, "path", ""),
            "user_id": getattr(user, "pk", "") if getattr(user, "is_authenticated", False) else "",
            "session_key": getattr(session, "session_key", "") if session else "",
        }


class NullDataLakeObjectEventWriter:
    def write_model_event(self, **kwargs):
        return None


class DataLakeObjectStateWriter:
    collection = DataLakeCollection(
        key="object_states",
        folder="EVENTS",
        entity_type="object_state",
        description="Append-only model state records emitted from Django save/delete signals for recoverability and object-level audit trails.",
        pii_classification="private",
    )

    def __init__(self, root):
        self.layout = SimpleObjectLakeLayout(root)
        self.record_builder = DataLakeRecordBuilder(redacted=False)

    @classmethod
    def from_settings(cls):
        root = (settings.MLADIS_DATASTORE_ROOT or "").strip()
        if not root:
            return NullDataLakeObjectStateWriter()
        return cls(root)

    def write_instance_state(self, *, event_name, instance, created=None, using="", update_fields=None):
        self.layout.initialize()
        now = timezone.now()
        entity_id = f"{instance._meta.label_lower}:{instance.pk}:{event_name}:{uuid4().hex[:8]}"
        record = self.record_builder.build(
            collection=self.collection,
            source_model=instance._meta.label,
            entity_id=entity_id,
            occurred_at=now,
            natural_keys=self._natural_keys(instance),
            data={
                "event_name": event_name,
                "object_model": instance._meta.label,
                "object_pk": str(instance.pk or ""),
                "created": created,
                "database": using or "",
                "update_fields": sorted(str(field) for field in update_fields) if update_fields else [],
                "object_state": self._serialize_instance(instance),
            },
        )
        object_path = self.layout.object_path(instance)
        history_path = self.layout.history_path_for_instance(instance)
        object_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        object_path.write_text(
            json.dumps(record, cls=DataLakeJsonEncoder, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        with history_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, cls=DataLakeJsonEncoder, sort_keys=True) + "\n")
        mirror = DataLakeDriveMirror.from_settings(self.layout.root)
        mirror.copy_path(object_path)
        mirror.copy_path(history_path)
        return object_path

    def _serialize_instance(self, instance):
        state = {}
        for field in instance._meta.fields:
            output_name = getattr(field, "attname", field.name)
            if self._is_sensitive_field(field.name) or self._is_sensitive_field(output_name):
                state[output_name] = "[redacted]"
                continue
            value = self._field_value(instance, field)
            state[output_name] = self.record_builder._clean(value)
        return state

    def _field_value(self, instance, field):
        if isinstance(field, django_models.FileField):
            file_value = getattr(instance, field.name, None)
            return getattr(file_value, "name", "") if file_value else ""
        if getattr(field, "is_relation", False) and getattr(field, "many_to_one", False):
            return getattr(instance, field.attname, None)
        return getattr(instance, field.name, None)

    def _natural_keys(self, instance):
        keys = {}
        for attr in ("request_key", "email", "phone", "slug", "code", "invoice_number", "username", "name", "title"):
            if not hasattr(instance, attr):
                continue
            value = getattr(instance, attr, "")
            if value is None or value == "":
                continue
            keys[attr] = str(value)
        return keys

    def _is_sensitive_field(self, name):
        lowered = (name or "").lower()
        return any(fragment in lowered for fragment in SENSITIVE_FIELD_FRAGMENTS)


class NullDataLakeObjectStateWriter:
    def write_instance_state(self, **kwargs):
        return None


class MLADISDataLakeExporter:
    COLLECTIONS = (
        DataLakeObjectEventWriter.collection,
        DataLakeObjectStateWriter.collection,
        DataLakeCollection(
            key="subscriptions",
            folder="CUSTOMERS",
            entity_type="subscription",
            description="Registered website accounts and linked social login/subscription identity metadata.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="customer_profiles",
            folder="CUSTOMERS",
            entity_type="customer_profile",
            description="Customer CRM profiles, segmentation, contact consent, and language preferences.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="airbnb_guest_records",
            folder="CUSTOMERS",
            entity_type="airbnb_guest_record",
            description="Imported Airbnb guest records and linked permission/feedback notes.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="customer_feedback",
            folder="CUSTOMERS",
            entity_type="customer_feedback",
            description="Guest feedback and review summaries tied to customers and stays.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="booking_requests",
            folder="BOOKINGS",
            entity_type="booking_request",
            description="User booking/request submissions, coupon use, status, and admin handling state.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="reservations",
            folder="BOOKINGS",
            entity_type="reservation",
            description="Reservation lifecycle records derived from booking inquiries after review/confirmation.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="agent_conversations",
            folder="BOOKINGAGENTS",
            entity_type="agent_conversation",
            description="Chatbot conversation logs, topics, language, and item context for agent improvement.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="anonymous_interactions",
            folder="INTERACTIONS",
            entity_type="conversation_interaction",
            description="Identity-free conversation turns used to improve guest-response quality.",
            pii_classification="anonymized",
        ),
        DataLakeCollection(
            key="agent_faq",
            folder="BOOKINGAGENTS",
            entity_type="agent_faq",
            description="Editable agent FAQ knowledge records used by the local booking assistant.",
            pii_classification="internal",
        ),
        DataLakeCollection(
            key="page_visits",
            folder="EVENTS",
            entity_type="page_visit",
            description="Lightweight website/app visit events for traffic analytics.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="damage_deposits",
            folder="TRANSACTIONS",
            entity_type="damage_deposit",
            description="Damage deposit checkout/authorization records across payment providers.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="reservation_payment_holds",
            folder="TRANSACTIONS",
            entity_type="reservation_payment_hold",
            description="Stay payment authorization holds created after the damage-deposit hold.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="donations",
            folder="TRANSACTIONS",
            entity_type="donation",
            description="Mission donation checkout records.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="invoices",
            folder="TRANSACTIONS",
            entity_type="invoice",
            description="Invoice headers and line-item totals for customer billing.",
            pii_classification="private",
        ),
        DataLakeCollection(
            key="promotions",
            folder="TRANSACTIONS",
            entity_type="promotion",
            description="Promotion campaigns, target segments, linked coupons, and delivery state.",
            pii_classification="internal",
        ),
        DataLakeCollection(
            key="inventory",
            folder="STAYS",
            entity_type="bookable_item",
            description="Bookable stays/services and Airbnb-facing inventory metadata.",
            pii_classification="internal",
        ),
        DataLakeCollection(
            key="availability_blocks",
            folder="STAYS",
            entity_type="availability_block",
            description="Manual calendar blocks that affect availability.",
            pii_classification="internal",
        ),
        DataLakeCollection(
            key="daily_price_overrides",
            folder="STAYS",
            entity_type="daily_price_override",
            description="Manual nightly price overrides by stay and date range.",
            pii_classification="internal",
        ),
        DataLakeCollection(
            key="maintenance_events",
            folder="MAINTENANCE",
            entity_type="maintenance_event",
            description="Maintenance, cleaning, repair, cost, time, vendor, and photo evidence records for tax and billing workflows.",
            pii_classification="private",
        ),
    )

    def __init__(self, root, *, redacted=False):
        self.layout = SimpleObjectLakeLayout(root)
        self.redacted = redacted
        self.record_builder = DataLakeRecordBuilder(redacted=redacted)
        self.writer = DataLakeJsonlWriter()

    def export(self, *, collections=None, schema_only=False, include_placeholders=False):
        export_run_id = timezone.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8]
        as_of = timezone.localdate()
        selected = self._selected_collections(collections)
        self.layout.initialize()
        self._write_catalog()

        collection_counts = {collection.key: 0 for collection in selected}
        if schema_only:
            if include_placeholders:
                for collection in selected:
                    placeholder_path = self._collection_file(collection, as_of, export_run_id, placeholder=True)
                    self.writer.write_records(
                        placeholder_path,
                        [
                            {
                                "schema_version": SCHEMA_VERSION,
                                "collection": collection.key,
                                "placeholder": True,
                                "message": "This file reserves the JSONL path. Run export_data_lake without --schema-only to write records.",
                            }
                        ],
                    )
            manifest_path = self._write_manifest(export_run_id, selected, collection_counts, schema_only=True)
            return DataLakeExportResult(export_run_id, self.layout.root, True, self.redacted, collection_counts, manifest_path)

        for collection in selected:
            records = list(self._records_for(collection))
            collection_counts[collection.key] = self.writer.write_records(
                self._collection_file(collection, as_of, export_run_id),
                records,
            )

        manifest_path = self._write_manifest(export_run_id, selected, collection_counts, schema_only=False)
        return DataLakeExportResult(export_run_id, self.layout.root, False, self.redacted, collection_counts, manifest_path)

    def _selected_collections(self, keys):
        if not keys:
            return list(self.COLLECTIONS)
        requested = {key.strip() for key in keys if key.strip()}
        collections = [collection for collection in self.COLLECTIONS if collection.key in requested]
        missing = sorted(requested - {collection.key for collection in collections})
        if missing:
            raise ValueError(f"Unknown data lake collection(s): {', '.join(missing)}")
        return collections

    def _collection_file(self, collection, as_of, export_run_id, *, placeholder=False):
        if placeholder:
            return self.layout.root / self.layout.folder_for_collection(collection) / f"{collection.key}-placeholder.jsonl"
        return self.layout.collection_path(collection)

    def _write_catalog(self):
        self.layout.catalog_path().write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "generated_at": timezone.now().isoformat(),
                    "layout": "simple-object-folders",
                    "folders": list(SIMPLE_OBJECT_LAKE_FOLDERS),
                    "collections": [
                        {
                            "key": collection.key,
                            "folder": self.layout.folder_for_collection(collection),
                            "entity_type": collection.entity_type,
                            "description": collection.description,
                            "pii_classification": collection.pii_classification,
                        }
                        for collection in self.COLLECTIONS
                    ],
                },
                indent=2,
                cls=DataLakeJsonEncoder,
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_manifest(self, export_run_id, collections, counts, *, schema_only):
        manifest_path = self.layout.manifest_path(export_run_id)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "export_run_id": export_run_id,
            "generated_at": timezone.now().isoformat(),
            "schema_only": schema_only,
            "redacted": self.redacted,
            "root": str(self.layout.root),
            "layout": "simple-object-folders",
            "collections": [
                {
                    "key": collection.key,
                    "folder": self.layout.folder_for_collection(collection),
                    "pii_classification": "redacted" if self.redacted else collection.pii_classification,
                    "count": counts.get(collection.key, 0),
                }
                for collection in collections
            ],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, cls=DataLakeJsonEncoder) + "\n", encoding="utf-8")
        return manifest_path

    def _records_for(self, collection):
        producer = getattr(self, f"_records_{collection.key}")
        return producer(collection)

    def _base_natural_keys(self, *, email="", phone="", slug="", code=""):
        natural_keys = {}
        if email:
            natural_keys["email" if not self.redacted else "email_hash"] = self.record_builder.identity(email)
        if phone:
            natural_keys["phone" if not self.redacted else "phone_hash"] = self.record_builder.identity(phone)
        if slug:
            natural_keys["slug"] = slug
        if code:
            natural_keys["code"] = code
        return natural_keys

    def _records_object_events(self, collection):
        return tuple()

    def _records_object_states(self, collection):
        return tuple()

    def _records_subscriptions(self, collection):
        User = get_user_model()
        try:
            from allauth.socialaccount.models import SocialAccount
        except ImportError:
            SocialAccount = None

        social_accounts = {}
        if SocialAccount:
            for account in SocialAccount.objects.select_related("user"):
                social_accounts.setdefault(account.user_id, []).append(
                    {
                        "provider": account.provider,
                        "uid_hash" if self.redacted else "uid": self.record_builder.identity(account.uid),
                    }
                )

        profiles = {
            profile.user_id: profile
            for profile in CustomerProfile.objects.filter(user__isnull=False)
        }
        for user in User.objects.order_by("date_joined", "id"):
            profile = profiles.get(user.id)
            data = {
                "user_id": user.id,
                "username_hash" if self.redacted else "username": self.record_builder.identity(user.username),
                "first_name": "" if self.redacted else user.first_name,
                "last_name": "" if self.redacted else user.last_name,
                **self.record_builder.contact_fields(email=user.email),
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
                "customer_profile_id": profile.id if profile else None,
                "customer_segment": profile.segment if profile else "",
                "preferred_language": profile.preferred_language if profile else "",
                "social_accounts": social_accounts.get(user.id, []),
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="auth.User",
                entity_id=user.id,
                occurred_at=user.date_joined,
                natural_keys=self._base_natural_keys(email=user.email),
                data=data,
            )

    def _records_customer_profiles(self, collection):
        for profile in CustomerProfile.objects.select_related("user").order_by("created_at", "id"):
            data = {
                "profile_id": profile.id,
                "user_id": profile.user_id,
                "name": "" if self.redacted else profile.name,
                **self.record_builder.contact_fields(email=profile.email, phone=profile.phone),
                "segment": profile.segment,
                "source": profile.source,
                "marketing_consent_status": profile.marketing_consent_status,
                "marketing_consent_requested_at": profile.marketing_consent_requested_at,
                "marketing_consent_at": profile.marketing_consent_at,
                "marketing_consent_source": profile.marketing_consent_source,
                "preferred_language": profile.preferred_language,
                "notes": "" if self.redacted else profile.notes,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.CustomerProfile",
                entity_id=profile.id,
                occurred_at=profile.created_at,
                natural_keys=self._base_natural_keys(email=profile.email, phone=profile.phone),
                data=data,
            )

    def _records_airbnb_guest_records(self, collection):
        queryset = AirbnbGuestRecord.objects.select_related("customer_profile", "item").order_by("created_at", "id")
        for record in queryset:
            data = {
                "airbnb_guest_record_id": record.id,
                "customer_profile_id": record.customer_profile_id,
                "item_id": record.item_id,
                "guest_name": "" if self.redacted else record.guest_name,
                **self.record_builder.contact_fields(email=record.email, phone=record.phone),
                "listing_title": record.listing_title,
                "airbnb_listing_id": record.airbnb_listing_id,
                "airbnb_thread_url": "" if self.redacted else record.airbnb_thread_url,
                "source_message_id": record.source_message_id,
                "source_email_subject": "" if self.redacted else record.source_email_subject,
                "source_email_timestamp": record.source_email_timestamp,
                "check_in": record.check_in,
                "check_out": record.check_out,
                "guests": record.guests,
                "message_excerpt": "" if self.redacted else record.message_excerpt,
                "feedback_summary": "" if self.redacted else record.feedback_summary,
                "rating": record.rating,
                "permission_notes": "" if self.redacted else record.permission_notes,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.AirbnbGuestRecord",
                entity_id=record.id,
                occurred_at=record.created_at,
                natural_keys=self._base_natural_keys(email=record.email, phone=record.phone),
                data=data,
            )

    def _records_customer_feedback(self, collection):
        queryset = CustomerFeedback.objects.select_related("customer_profile", "airbnb_guest_record", "item").order_by("created_at", "id")
        for feedback in queryset:
            data = {
                "feedback_id": feedback.id,
                "customer_profile_id": feedback.customer_profile_id,
                "airbnb_guest_record_id": feedback.airbnb_guest_record_id,
                "item_id": feedback.item_id,
                "source": feedback.source,
                "source_label": feedback.source_label,
                "source_url": "" if self.redacted else feedback.source_url,
                "guest_name": "" if self.redacted else feedback.guest_name,
                **self.record_builder.contact_fields(email=feedback.email, phone=feedback.phone),
                "rating": feedback.rating,
                "feedback_text": "" if self.redacted else feedback.feedback_text,
                "feedback_summary": "" if self.redacted else feedback.feedback_summary,
                "permission_notes": "" if self.redacted else feedback.permission_notes,
                "is_public": feedback.is_public,
                "published_at": feedback.published_at,
                "created_at": feedback.created_at,
                "updated_at": feedback.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.CustomerFeedback",
                entity_id=feedback.id,
                occurred_at=feedback.created_at,
                natural_keys=self._base_natural_keys(email=feedback.email, phone=feedback.phone),
                data=data,
            )

    def _booking_record_data(self, inquiry):
        return {
            "booking_inquiry_id": inquiry.id,
            "user_id": inquiry.user_id,
            "customer_profile_id": inquiry.customer_profile_id,
            "item_id": inquiry.item_id,
            "item_name": inquiry.item.business_display_name if inquiry.item else "",
            "guest_name": "" if self.redacted else inquiry.guest_name,
            **self.record_builder.contact_fields(email=inquiry.email, phone=inquiry.phone),
            "check_in": inquiry.check_in,
            "check_out": inquiry.check_out,
            "nights": inquiry.nights,
            "guests": inquiry.guests,
            "message": "" if self.redacted else inquiry.message,
            "coupon_id": inquiry.coupon_id,
            "coupon_code": inquiry.coupon_code,
            "cancellation_policy_id": inquiry.cancellation_policy_id,
            "status": inquiry.status,
            "subtotal_cents": inquiry.subtotal_cents,
            "discount_cents": inquiry.discount_cents,
            "reservation_payment_cents": inquiry.reservation_payment_cents,
            "deposit_cents": inquiry.deposit_cents,
            "total_cents": inquiry.total_cents,
            "currency": inquiry.currency,
            "is_admin_test": inquiry.is_admin_test,
            "is_blacklist_flagged": inquiry.is_blacklist_flagged,
            "canceled_at": inquiry.canceled_at,
            "cancellation_reason": "" if self.redacted else inquiry.cancellation_reason,
            "email_sent_at": inquiry.email_sent_at,
            "email_delivery_status": inquiry.email_delivery_status,
            "email_error": "" if self.redacted else inquiry.email_error,
            "admin_notes": "" if self.redacted else inquiry.admin_notes,
            "created_at": inquiry.created_at,
            "updated_at": inquiry.updated_at,
        }

    def _records_booking_requests(self, collection):
        queryset = BookingInquiry.objects.select_related("user", "customer_profile", "item", "coupon", "cancellation_policy").order_by("created_at", "id")
        for inquiry in queryset:
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.BookingInquiry",
                entity_id=inquiry.id,
                occurred_at=inquiry.created_at,
                natural_keys=self._base_natural_keys(email=inquiry.email, phone=inquiry.phone),
                data=self._booking_record_data(inquiry),
            )

    def _records_reservations(self, collection):
        statuses = {BookingStatus.QUOTED, BookingStatus.CONFIRMED, BookingStatus.CANCELED, BookingStatus.DECLINED}
        queryset = BookingInquiry.objects.filter(status__in=statuses).select_related("item", "customer_profile").order_by("created_at", "id")
        for inquiry in queryset:
            data = self._booking_record_data(inquiry)
            data["reservation_state"] = "active" if inquiry.status == BookingStatus.CONFIRMED else inquiry.status
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.BookingInquiry",
                entity_id=inquiry.id,
                occurred_at=inquiry.created_at,
                natural_keys=self._base_natural_keys(email=inquiry.email, phone=inquiry.phone),
                data=data,
            )

    def _records_agent_conversations(self, collection):
        # Keep the legacy collection key for consumers that still request it,
        # but use the same identity-free projection as INTERACTIONS. New
        # conversation content must not re-enter the lake through this path.
        from .interaction_lake import AnonymousInteractionLakeWriter

        writer = AnonymousInteractionLakeWriter(self.layout.root)
        queryset = AgentConversation.objects.select_related("user").order_by("created_at", "id")
        for conversation in queryset:
            record = writer.build_agent_record(conversation)
            record["collection"] = collection.key
            record["entity_type"] = collection.entity_type
            record["pii_classification"] = "anonymized"
            if self.redacted:
                for turn in record.get("data", {}).get("turns", []):
                    turn["text"] = "[redacted]"
            yield record

    def _records_anonymous_interactions(self, collection):
        from .interaction_lake import AnonymousInteractionLakeWriter

        writer = AnonymousInteractionLakeWriter(self.layout.root)
        queryset = AgentConversation.objects.select_related("user").order_by("created_at", "id")
        for conversation in queryset:
            record = writer.build_agent_record(conversation)
            if self.redacted:
                for turn in record.get("data", {}).get("turns", []):
                    turn["text"] = "[redacted]"
            yield record

    def _records_agent_faq(self, collection):
        for faq in AgentFAQ.objects.select_related("item").order_by("category", "priority", "id"):
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.AgentFAQ",
                entity_id=faq.id,
                occurred_at=faq.created_at,
                natural_keys={"category": faq.category, "language": faq.language},
                data={
                    "agent_faq_id": faq.id,
                    "category": faq.category,
                    "question": faq.question,
                    "answer": faq.answer,
                    "keywords": faq.keywords,
                    "item_id": faq.item_id,
                    "language": faq.language,
                    "min_score": faq.min_score,
                    "priority": faq.priority,
                    "is_active": faq.is_active,
                    "created_at": faq.created_at,
                    "updated_at": faq.updated_at,
                },
            )

    def _records_page_visits(self, collection):
        queryset = PageVisit.objects.select_related("user").order_by("created_at", "id")
        for visit in queryset:
            email = visit.user.email if visit.user else ""
            data = {
                "page_visit_id": visit.id,
                "path": visit.path,
                "user_id": visit.user_id,
                "session_key_hash" if self.redacted else "session_key": self.record_builder.identity(visit.session_key),
                "language": visit.language,
                "user_agent": "" if self.redacted else visit.user_agent,
                "created_at": visit.created_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.PageVisit",
                entity_id=visit.id,
                occurred_at=visit.created_at,
                natural_keys=self._base_natural_keys(email=email),
                data=data,
            )

    def _records_damage_deposits(self, collection):
        queryset = DamageDeposit.objects.select_related("inquiry", "item").order_by("created_at", "id")
        for deposit in queryset:
            data = {
                "damage_deposit_id": deposit.id,
                "booking_inquiry_id": deposit.inquiry_id,
                "item_id": deposit.item_id,
                "guest_name": "" if self.redacted else deposit.guest_name,
                **self.record_builder.contact_fields(email=deposit.email),
                "amount_cents": deposit.amount_cents,
                "currency": deposit.currency,
                "payment_provider": deposit.payment_provider,
                "status": deposit.status,
                "stripe_checkout_session_id": "" if self.redacted else deposit.stripe_checkout_session_id,
                "stripe_payment_intent_id": "" if self.redacted else deposit.stripe_payment_intent_id,
                "paypal_order_id": "" if self.redacted else deposit.paypal_order_id,
                "paypal_authorization_id": "" if self.redacted else deposit.paypal_authorization_id,
                "checkout_url": "" if self.redacted else deposit.checkout_url,
                "notes": "" if self.redacted else deposit.notes,
                "created_at": deposit.created_at,
                "updated_at": deposit.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.DamageDeposit",
                entity_id=deposit.id,
                occurred_at=deposit.created_at,
                natural_keys=self._base_natural_keys(email=deposit.email),
                data=data,
            )

    def _records_reservation_payment_holds(self, collection):
        queryset = ReservationPaymentHold.objects.select_related("inquiry", "item").order_by("created_at", "id")
        for hold in queryset:
            data = {
                "reservation_payment_hold_id": hold.id,
                "booking_inquiry_id": hold.inquiry_id,
                "item_id": hold.item_id,
                "guest_name": "" if self.redacted else hold.guest_name,
                **self.record_builder.contact_fields(email=hold.email),
                "amount_cents": hold.amount_cents,
                "currency": hold.currency,
                "payment_provider": hold.payment_provider,
                "status": hold.status,
                "stripe_checkout_session_id": "" if self.redacted else hold.stripe_checkout_session_id,
                "stripe_payment_intent_id": "" if self.redacted else hold.stripe_payment_intent_id,
                "checkout_url": "" if self.redacted else hold.checkout_url,
                "capture_after": hold.capture_after,
                "notes": "" if self.redacted else hold.notes,
                "created_at": hold.created_at,
                "updated_at": hold.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.ReservationPaymentHold",
                entity_id=hold.id,
                occurred_at=hold.created_at,
                natural_keys=self._base_natural_keys(email=hold.email),
                data=data,
            )

    def _records_donations(self, collection):
        queryset = Donation.objects.select_related("cause").order_by("created_at", "id")
        for donation in queryset:
            data = {
                "donation_id": donation.id,
                "cause_id": donation.cause_id,
                "cause_name": donation.cause.name if donation.cause else "",
                "donor_name": "" if self.redacted else donation.donor_name,
                **self.record_builder.contact_fields(email=donation.email),
                "amount_cents": donation.amount_cents,
                "currency": donation.currency,
                "status": donation.status,
                "stripe_checkout_session_id": "" if self.redacted else donation.stripe_checkout_session_id,
                "stripe_payment_intent_id": "" if self.redacted else donation.stripe_payment_intent_id,
                "checkout_url": "" if self.redacted else donation.checkout_url,
                "notes": "" if self.redacted else donation.notes,
                "created_at": donation.created_at,
                "updated_at": donation.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.Donation",
                entity_id=donation.id,
                occurred_at=donation.created_at,
                natural_keys=self._base_natural_keys(email=donation.email),
                data=data,
            )

    def _records_invoices(self, collection):
        queryset = Invoice.objects.select_related("inquiry", "customer_profile").prefetch_related("line_items").order_by("created_at", "id")
        for invoice in queryset:
            data = {
                "invoice_id": invoice.id,
                "booking_inquiry_id": invoice.inquiry_id,
                "customer_profile_id": invoice.customer_profile_id,
                "invoice_number": invoice.invoice_number,
                "public_token": "" if self.redacted else str(invoice.public_token),
                "recipient_name": "" if self.redacted else invoice.recipient_name,
                **self.record_builder.contact_fields(email=invoice.recipient_email),
                "status": invoice.status,
                "issue_date": invoice.issue_date,
                "due_date": invoice.due_date,
                "currency": invoice.currency,
                "subtotal_cents": invoice.subtotal_cents,
                "discount_cents": invoice.discount_cents,
                "deposit_cents": invoice.deposit_cents,
                "total_cents": invoice.total_cents,
                "logo_snapshot_url": invoice.logo_snapshot_url,
                "notes": "" if self.redacted else invoice.notes,
                "sent_at": invoice.sent_at,
                "email_status": invoice.email_status,
                "email_error": "" if self.redacted else invoice.email_error,
                "line_items": [
                    {
                        "description": line.description,
                        "quantity": line.quantity,
                        "unit_amount_cents": line.unit_amount_cents,
                        "amount_cents": line.amount_cents,
                        "sort_order": line.sort_order,
                    }
                    for line in invoice.line_items.all()
                ],
                "created_at": invoice.created_at,
                "updated_at": invoice.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.Invoice",
                entity_id=invoice.id,
                occurred_at=invoice.created_at,
                natural_keys=self._base_natural_keys(email=invoice.recipient_email, code=invoice.invoice_number),
                data=data,
            )

    def _records_promotions(self, collection):
        queryset = Promotion.objects.select_related("coupon", "created_by").prefetch_related("recipients").order_by("created_at", "id")
        for promotion in queryset:
            data = {
                "promotion_id": promotion.id,
                "title": promotion.title,
                "subject": promotion.subject,
                "message": promotion.message,
                "discount_percent": promotion.discount_percent,
                "coupon_id": promotion.coupon_id,
                "coupon_code": promotion.coupon.code if promotion.coupon else "",
                "target_segment": promotion.target_segment,
                "status": promotion.status,
                "created_by_id": promotion.created_by_id,
                "sent_at": promotion.sent_at,
                "recipients": [
                    {
                        "customer_profile_id": recipient.customer_profile_id,
                        "name": "" if self.redacted else recipient.name,
                        **self.record_builder.contact_fields(email=recipient.email),
                        "status": recipient.status,
                        "error": "" if self.redacted else recipient.error,
                        "sent_at": recipient.sent_at,
                    }
                    for recipient in promotion.recipients.all()
                ],
                "created_at": promotion.created_at,
                "updated_at": promotion.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.Promotion",
                entity_id=promotion.id,
                occurred_at=promotion.created_at,
                data=data,
            )

    def _records_inventory(self, collection):
        for item in BookableItem.objects.order_by("category", "name", "id"):
            data = {
                "bookable_item_id": item.id,
                "name": item.name,
                "business_display_name": item.business_display_name,
                "slug": item.slug,
                "category": item.category,
                "short_description": item.short_description,
                "marketing_headline": item.marketing_headline,
                "location_label": item.location_label,
                "starting_price": item.starting_price,
                "price_unit": item.price_unit,
                "max_guests": item.max_guests,
                "bedrooms": item.bedrooms,
                "beds": item.beds,
                "bathrooms": item.bathrooms,
                "airbnb_listing_id": item.airbnb_listing_id,
                "airbnb_url": item.airbnb_url,
                "airbnb_rating": item.airbnb_rating,
                "review_count": item.review_count,
                "is_featured": item.is_featured,
                "is_active": item.is_active,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.BookableItem",
                entity_id=item.id,
                occurred_at=item.created_at,
                natural_keys=self._base_natural_keys(slug=item.slug),
                data=data,
            )

    def _records_availability_blocks(self, collection):
        for block in AvailabilityBlock.objects.select_related("item").order_by("created_at", "id"):
            data = {
                "availability_block_id": block.id,
                "item_id": block.item_id,
                "item_name": block.item.business_display_name if block.item else "",
                "start_date": block.start_date,
                "end_date": block.end_date,
                "reason": block.reason,
                "notes": "" if self.redacted else block.notes,
                "is_active": block.is_active,
                "created_at": block.created_at,
                "updated_at": block.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.AvailabilityBlock",
                entity_id=block.id,
                occurred_at=block.created_at,
                data=data,
            )

    def _records_daily_price_overrides(self, collection):
        for override in DailyPriceOverride.objects.select_related("item").order_by("created_at", "id"):
            data = {
                "daily_price_override_id": override.id,
                "item_id": override.item_id,
                "item_name": override.item.business_display_name if override.item else "",
                "start_date": override.start_date,
                "end_date": override.end_date,
                "nightly_price": override.nightly_price,
                "label": override.label,
                "notes": "" if self.redacted else override.notes,
                "is_active": override.is_active,
                "created_at": override.created_at,
                "updated_at": override.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.DailyPriceOverride",
                entity_id=override.id,
                occurred_at=override.created_at,
                data=data,
            )

    def _records_maintenance_events(self, collection):
        queryset = (
            MaintenanceEvent.objects.select_related("item", "booking", "created_by", "approved_by")
            .prefetch_related("photos")
            .order_by("created_at", "id")
        )
        for event in queryset:
            booking = event.booking
            data = {
                "maintenance_event_id": str(event.id),
                "item_id": event.item_id,
                "item_name": event.item.business_display_name if event.item else "",
                "booking_inquiry_id": event.booking_id,
                "reservation": {
                    "request_key": booking.request_key if booking else "",
                    "guest_name": "" if self.redacted or not booking else booking.guest_name,
                    "guest_email": "" if self.redacted or not booking else booking.email,
                    "check_in": booking.check_in if booking else None,
                    "check_out": booking.check_out if booking else None,
                    "nights": booking.nights if booking else 0,
                    "guests": booking.guests if booking else 0,
                    "status": booking.status if booking else "",
                },
                "title": event.title,
                "work_type": event.work_type,
                "status": event.status,
                "cost_amount": event.cost_amount,
                "cost_currency": event.cost_currency,
                "reported_at": event.reported_at,
                "started_at": event.started_at,
                "completed_at": event.completed_at,
                "duration_minutes": event.duration_minutes,
                "timezone_name": event.timezone_name,
                "vendor_name": "" if self.redacted else event.vendor_name,
                "vendor_contact": "" if self.redacted else event.vendor_contact,
                "payment_status": event.payment_status,
                "invoice_number": event.invoice_number,
                "proof_of_payment_ref": "" if self.redacted else event.proof_of_payment_ref,
                "tax_category_code": event.tax_category_code,
                "description": "" if self.redacted else event.description,
                "admin_notes": "" if self.redacted else event.admin_notes,
                "created_by_id": event.created_by_id,
                "approved_by_id": event.approved_by_id,
                "photo_count": event.photo_count,
                "is_tax_ready": event.is_tax_ready,
                "photos": [
                    {
                        "photo_id": str(photo.id),
                        "caption": photo.caption,
                        "sort_order": photo.sort_order,
                        "is_cover": photo.is_cover,
                        "checksum_sha256": photo.checksum_sha256,
                        "mime_type": photo.mime_type,
                        "file_size_bytes": photo.file_size_bytes,
                        "captured_at": photo.captured_at,
                        "uploaded_at": photo.uploaded_at,
                        "image_path": "" if self.redacted else getattr(photo.image, "name", ""),
                    }
                    for photo in event.photos.all()
                ],
                "created_at": event.created_at,
                "updated_at": event.updated_at,
            }
            yield self.record_builder.build(
                collection=collection,
                source_model="bookings.MaintenanceEvent",
                entity_id=event.id,
                occurred_at=event.reported_at or event.created_at,
                natural_keys={
                    "item_slug": event.item.slug if event.item else "",
                    "request_key": booking.request_key if booking else "",
                    "work_type": event.work_type,
                },
                data=data,
            )
