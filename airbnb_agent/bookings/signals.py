from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


LIVE_OBJECT_STATE_APP_LABELS = {"bookings", "operations", "auth", "account", "socialaccount"}
LIVE_OBJECT_STATE_EXCLUDED_MODELS = {
    "bookings.PageVisit",
    # Conversation text is written through the identity-free interaction lake
    # instead of the generic model-state serializer.
    "bookings.AgentConversation",
}


@receiver(user_logged_in)
def promote_known_admin_email(sender, request, user, **kwargs):
    from .services import AdminAccessService

    AdminAccessService().apply_to_user(user)


@receiver(post_save)
def write_data_lake_object_state_on_save(sender, instance, created=False, raw=False, using=None, update_fields=None, **kwargs):
    if raw:
        return
    if _is_agent_conversation(instance) and created:
        _write_anonymous_interaction(instance)
    if not _should_write_object_state(instance):
        return
    _write_object_state(
        event_name="object.created" if created else "object.updated",
        instance=instance,
        created=created,
        using=using,
        update_fields=update_fields,
    )


@receiver(post_delete)
def write_data_lake_object_state_on_delete(sender, instance, using=None, **kwargs):
    if not _should_write_object_state(instance):
        return
    _write_object_state(
        event_name="object.deleted",
        instance=instance,
        created=False,
        using=using,
        update_fields=None,
    )


def _should_write_object_state(instance):
    meta = instance._meta
    if meta.app_label not in LIVE_OBJECT_STATE_APP_LABELS:
        return False
    if meta.label in LIVE_OBJECT_STATE_EXCLUDED_MODELS:
        return False
    return True


def _is_agent_conversation(instance):
    return instance._meta.label == "bookings.AgentConversation"


def _write_anonymous_interaction(instance):
    try:
        from .interaction_lake import AnonymousInteractionLakeWriter

        AnonymousInteractionLakeWriter.from_settings().write_agent_conversation(instance)
    except Exception:
        # Learning-lake persistence must never break the transactional app path.
        return


def _write_object_state(*, event_name, instance, created, using, update_fields):
    try:
        from .data_lake import DataLakeObjectStateWriter

        DataLakeObjectStateWriter.from_settings().write_instance_state(
            event_name=event_name,
            instance=instance,
            created=created,
            using=using or "",
            update_fields=update_fields,
        )
    except Exception:
        # Data-lake writes must never break the transactional app path.
        return
