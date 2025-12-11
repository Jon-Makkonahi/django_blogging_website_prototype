from uuid import uuid4
from pytils.translit import slugify


def unique_slugify(instance, slug, slug_field):
    """
    Генератор уникальных SLUG для моделей, в случае существования такого SLUG.
    """
    model = instance.__class__
    if not slug_field:
        slug_field = slugify(slug)
    if model.objects.filter(slug=slug_field).exclude(id=instance.id).exists():
        slug_field = f'{slugify(slug)}-{uuid4().hex[:8]}'
    return slug_field
