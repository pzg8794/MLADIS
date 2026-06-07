from rest_framework import serializers
from .models import MaintenanceEvent, MaintenancePhoto


class MaintenancePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenancePhoto
        fields = ["id", "image", "caption", "created_at"]
        read_only_fields = ["id", "created_at"]


class MaintenanceEventSerializer(serializers.ModelSerializer):
    """
    Accepts nested 'cost' and 'time' dicts plus a list of 'pictures' on write.
    Returns flattened cost/time/photos on read for agent consumption.
    """

    # Write-only structured inputs
    cost = serializers.DictField(child=serializers.CharField(), write_only=True)
    time = serializers.DictField(child=serializers.CharField(), write_only=True)
    pictures = MaintenancePhotoSerializer(many=True, write_only=True, required=True)

    # Read-only structured outputs
    cost_out = serializers.SerializerMethodField(read_only=True)
    time_out = serializers.SerializerMethodField(read_only=True)
    photos = MaintenancePhotoSerializer(source="photos", many=True, read_only=True)

    class Meta:
        model = MaintenanceEvent
        fields = [
            "id",
            "property",
            "booking",
            "title",
            "category",
            "status",
            "description",
            "tax_category_code",
            # write inputs
            "cost",
            "time",
            "pictures",
            # read outputs
            "cost_out",
            "time_out",
            "photos",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "cost_out",
            "time_out",
            "photos",
        ]

    # -----------------------------------------------------------------------
    # Validation — enforce the four required attributes
    # -----------------------------------------------------------------------
    def validate(self, attrs):
        cost = attrs.get("cost") or {}
        time = attrs.get("time") or {}
        pictures = attrs.get("pictures") or []

        if not attrs.get("title", "").strip():
            raise serializers.ValidationError({"title": "Title is required."})
        if "amount" not in cost:
            raise serializers.ValidationError({"cost": "cost.amount is required."})
        if "currency" not in cost:
            raise serializers.ValidationError({"cost": "cost.currency is required."})
        if "start_at" not in time:
            raise serializers.ValidationError({"time": "time.start_at is required."})
        if not pictures:
            raise serializers.ValidationError(
                {"pictures": "At least one picture is required."}
            )
        return attrs

    # -----------------------------------------------------------------------
    # Create — unpack structured fields into flat model fields
    # -----------------------------------------------------------------------
    def create(self, validated_data):
        from django.utils.dateparse import parse_datetime

        request = self.context["request"]
        cost = validated_data.pop("cost")
        time_data = validated_data.pop("time")
        pictures_data = validated_data.pop("pictures")

        validated_data["cost_amount"] = cost["amount"]
        validated_data["cost_currency"] = cost.get("currency", "USD")
        validated_data["start_at"] = parse_datetime(time_data["start_at"]) or time_data["start_at"]
        if "end_at" in time_data and time_data["end_at"]:
            validated_data["end_at"] = parse_datetime(time_data["end_at"]) or time_data["end_at"]

        event = MaintenanceEvent.objects.create(
            created_by=request.user, **validated_data
        )
        for photo_data in pictures_data:
            MaintenancePhoto.objects.create(event=event, **photo_data)

        return event

    # -----------------------------------------------------------------------
    # Read helpers
    # -----------------------------------------------------------------------
    def get_cost_out(self, obj):
        return {"amount": str(obj.cost_amount), "currency": obj.cost_currency}

    def get_time_out(self, obj):
        return {
            "start_at": obj.start_at.isoformat() if obj.start_at else None,
            "end_at": obj.end_at.isoformat() if obj.end_at else None,
            "duration_minutes": obj.duration_minutes,
        }


class MaintenanceInvoicePayloadSerializer(serializers.Serializer):
    """Wraps the agent-friendly JSON payload for the invoice/tax document action."""
    payload = serializers.JSONField()
