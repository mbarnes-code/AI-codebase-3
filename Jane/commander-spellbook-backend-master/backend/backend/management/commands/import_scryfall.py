import json, requests
from django.core.management.base import BaseCommand
from django.db import transaction
from spellbook.models import Card   # adjust if Card lives elsewhere

BULK_API  = "https://api.scryfall.com/bulk-data"
BULK_TYPE = "default_cards"         # or "oracle_cards"

class Command(BaseCommand):
    help = "Sync Scryfall bulk data with the Card table (add / update only)."

    @transaction.atomic
    def handle(self, *args, **opts):
        # 1) locate bulk-data file
        meta = requests.get(BULK_API, timeout=30).json()
        download_uri = next(i["download_uri"] for i in meta["data"]
                            if i["type"] == BULK_TYPE)
        self.stdout.write(f"Downloading {download_uri} …")
        cards_json = requests.get(download_uri, timeout=120).json()

        # 2) lookup of existing cards {oracle_id: Card instance}
        existing = {
            str(c.oracle_id): c
            for c in Card.objects.all().only(
                "id", "oracle_id", "name", "oracle_text", "type_line"
            )
        }

        new_objs  = []
        to_update = []
        created = updated = skipped = 0

        for c in cards_json:
            oid         = c["id"]
            name        = c["name"]
            oracle_text = c.get("oracle_text", "")
            type_line   = c.get("type_line", "")

            if oid in existing:
                card = existing[oid]
                if (card.name, card.oracle_text, card.type_line) != (
                    name, oracle_text, type_line
                ):
                    card.name        = name
                    card.oracle_text = oracle_text
                    card.type_line   = type_line
                    to_update.append(card)
                    updated += 1
                else:
                    skipped += 1
            else:
                new_objs.append(
                    Card(
                        oracle_id=oid,
                        name=name,
                        oracle_text=oracle_text,
                        type_line=type_line,
                    )
                )
                created += 1

            # flush in batches
            if len(new_objs) >= 1000:
                Card.objects.bulk_create(new_objs, ignore_conflicts=True)
                new_objs.clear()
            if len(to_update) >= 1000:
                Card.objects.bulk_update(
                    to_update, ["name", "oracle_text", "type_line"]
                )
                to_update.clear()

        # flush any remainder
        if new_objs:
            Card.objects.bulk_create(new_objs, ignore_conflicts=True)
        if to_update:
            Card.objects.bulk_update(
                to_update, ["name", "oracle_text", "type_line"]
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync complete — created: {created}, updated: {updated}, "
                f"unchanged: {skipped}"
            )
        )
