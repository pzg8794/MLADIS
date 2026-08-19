"""Prepare and transition one private Airbnb auto-response job."""

import json
import os
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from bookings.airbnb_outbound import OutboundAuthorizationService, OutboundAuthorizationError
from bookings.airbnb_response_workflow import AirbnbResponseWorkflow, ResponseWorkflowError
from bookings.models import BookableItem


class Command(BaseCommand):
    help = "Prepare, claim, complete, or quarantine one private Airbnb response job."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=("prepare", "claim", "complete", "uncertain"))
        parser.add_argument("--input", required=True)
        parser.add_argument("--output", required=True)
        parser.add_argument("--authorize-low-stakes", action="store_true")

    def handle(self, *args, **options):
        try:
            payload = self._read_private_json(options["input"])
            result = self._execute(
                options["action"],
                payload,
                authorize_low_stakes=options["authorize_low_stakes"],
            )
            self._write_private_json(options["output"], result)
        except (OSError, ValueError, TypeError, ResponseWorkflowError, OutboundAuthorizationError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            json.dumps(
                {
                    "action": options["action"],
                    "status": result.get("status"),
                    "output": str(Path(options["output"]).expanduser().resolve()),
                },
                sort_keys=True,
            )
        )

    def _execute(self, action, payload, *, authorize_low_stakes):
        authorization_service = OutboundAuthorizationService()
        if action == "prepare":
            item = self._resolve_item(payload)
            workflow = AirbnbResponseWorkflow(authorization_service=authorization_service)
            draft = workflow.draft(
                payload.get("latest_message"),
                item_id=item.pk if item else None,
            )
            result = {
                "status": "held",
                "topic": draft.topic,
                "mode": draft.mode,
                "low_stakes": draft.low_stakes,
                "grounding_status": draft.grounding_status,
                "risk_reasons": list(draft.risk_reasons),
                "draft_hash": draft.draft_hash,
                "item_id": draft.item_id,
                "rules_digest": draft.rules_digest,
                "reply": draft.reply,
                "authorization_id": "",
                "hold_reason": "automatic_authorization_not_requested",
            }
            if authorize_low_stakes:
                try:
                    authorization = workflow.authorize_automatic(
                        draft,
                        thread_key=payload.get("thread_key"),
                        latest_message=payload.get("latest_message"),
                    )
                except ResponseWorkflowError as error:
                    result["hold_reason"] = str(error)
                else:
                    result.update(
                        {
                            "status": "authorized",
                            "authorization_id": authorization.authorization_id,
                            "hold_reason": "",
                            "expires_at": authorization.expires_at,
                        }
                    )
            return result

        authorization_id = str(payload.get("authorization_id") or "")
        if action == "claim":
            authorization = authorization_service.claim(
                authorization_id,
                thread_key=payload.get("thread_key"),
                latest_message=payload.get("latest_message"),
                draft_hash=payload.get("draft_hash"),
            )
        elif action == "complete":
            authorization = authorization_service.complete(
                authorization_id,
                provider_message_id=payload.get("provider_message_id"),
            )
        else:
            authorization = authorization_service.mark_uncertain(
                authorization_id,
                reason=payload.get("reason") or "browser_delivery_not_verified",
            )
        return {
            "status": authorization.status,
            "authorization_id": authorization.authorization_id,
        }

    @staticmethod
    def _resolve_item(payload):
        item_id = payload.get("item_id")
        if item_id:
            item = BookableItem.objects.filter(pk=item_id, is_active=True).first()
            if item:
                return item
        listing_id = str(payload.get("listing_id") or "").strip()
        if listing_id:
            item = BookableItem.objects.filter(
                airbnb_listing_id=listing_id,
                is_active=True,
            ).first()
            if item:
                return item
        hint = re.sub(r"\s+", " ", str(payload.get("listing_hint") or "")).casefold()
        if not hint:
            return None
        candidates = []
        for item in BookableItem.objects.filter(is_active=True):
            labels = {item.name.casefold(), item.slug.casefold().replace("-", " ")}
            labels.update(re.findall(r"\bg[- ]?\d{3}\b", item.name.casefold()))
            if any(label and label in hint for label in labels):
                candidates.append(item)
        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def _read_private_json(value):
        path = Path(value).expanduser().resolve()
        mode = path.stat().st_mode & 0o777
        if mode & 0o077:
            raise CommandError("Private response input must not be group/world accessible.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise CommandError("Private response input must be a JSON object.")
        return payload

    @staticmethod
    def _write_private_json(value, payload):
        path = Path(value).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.chmod(0o600)
        temporary.replace(path)
        os.chmod(path, 0o600)
