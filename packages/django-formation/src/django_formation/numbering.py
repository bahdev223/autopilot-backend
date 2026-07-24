from django.utils import timezone


def sequential_number(*, queryset, prefix):
    """Generate a yearly sequence while the caller holds an establishment lock."""
    year = timezone.localdate().year
    last = queryset.filter(**{}).order_by("-created_at").first()
    sequence = 0
    if last:
        value = getattr(last, "matricule", None) or getattr(last, "numero", "")
        try:
            sequence = int(value.rsplit("-", 1)[-1])
        except (TypeError, ValueError):
            sequence = 0
    return f"{prefix}-{year}-{sequence + 1:06d}"
