import json
import requests
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from spellbook.models import Combo

URL = "https://json.commanderspellbook.com/variants.json"

def camel_to_snake(name: str) -> str:
    """Convert mixedCase or camelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class Command(BaseCommand):
    help = "Dynamically import ALL top-level combo fields from variants.json"

    def handle(self, *args, **opts):
        self.stdout.write("Fetching variants.json …")
        data = requests.get(URL, timeout=120).json()
        variants = data.get("variants", [])
        if not variants:
            self.stderr.write("No 'variants' array found—aborting.")
            return

        # Figure out which fields on Combo we can set directly
        model_fields = {
            f.name: f
            for f in Combo._meta.get_fields()
            if not f.many_to_many and not f.one_to_many
        }

        created = updated = 0

        with transaction.atomic():
            for v in variants:
                cid = v.get("id")
                if not cid:
                    continue

                defaults = {}
                for key, val in v.items():
                    snake = camel_to_snake(key)
                    if snake in model_fields and snake != 'name' and snake != 'id':
                        # if list or dict, store JSON string
                        if isinstance(val, (list, dict)):
                            defaults[snake] = json.dumps(val)
                        else:
                            defaults[snake] = val

                # Upsert: use name=cid as unique key
                obj, is_new = Combo.objects.update_or_create(
                    name=cid,
                    defaults=defaults
                )
                if is_new:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete — created: {created}, updated: {updated}"
            )
        )
