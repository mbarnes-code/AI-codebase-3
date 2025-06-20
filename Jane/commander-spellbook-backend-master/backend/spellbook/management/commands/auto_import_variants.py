from django.core.management.base import BaseCommand
from django.db import transaction
from spellbook.models import Variant, Card
from decimal import Decimal
import json
import os

class Command(BaseCommand):
    help = 'Auto-import variants from mounted data folder'
    
    def handle(self, *args, **options):
        data_file = '/app/data/variants.json'
        
        if not os.path.exists(data_file):
            self.stdout.write(self.style.WARNING('No variants file found at /app/data/variants.json'))
            return
            
        if Variant.objects.count() > 0:
            self.stdout.write(self.style.WARNING('Variants already exist, skipping auto-import'))
            return
            
        self.stdout.write('Auto-importing variants...')
        self.import_variants(data_file)
    
    def import_variants(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        variants_data = data['variants']
        self.stdout.write(f'Found {len(variants_data)} variants to import')
        
        imported = 0
        batch_size = 50
        
        for i in range(0, len(variants_data), batch_size):
            batch = variants_data[i:i+batch_size]
            
            with transaction.atomic():
                for variant_data in batch:
                    try:
                        # Create cards first
                        for card_usage in variant_data.get('uses', []):
                            card_info = card_usage.get('card', {})
                            if card_info.get('id'):
                                card, created = Card.objects.get_or_create(
                                    id=card_info['id'],
                                    defaults={
                                        'name': card_info.get('name', ''),
                                        'oracle_id': card_info.get('oracleId', ''),
                                        'type_line': card_info.get('typeLine', ''),
                                        'spoiler': card_info.get('spoiler', False)
                                    }
                                )
                        
                        # Create variant
                        prices = variant_data.get('prices', {})
                        variant, created = Variant.objects.get_or_create(
                            id=variant_data.get('id'),
                            defaults={
                                'description': variant_data.get('description', ''),
                                'mana_needed': variant_data.get('manaNeeded', ''),
                                'mana_value_needed': variant_data.get('manaValueNeeded', 0),
                                'notable_prerequisites': variant_data.get('notablePrerequisites', ''),
                                'status': variant_data.get('status', 'OK'),
                                'spoiler': variant_data.get('spoiler', False),
                                'identity': variant_data.get('identity', ''),
                                'bracket_tag': variant_data.get('bracketTag', ''),
                                'price_tcgplayer': Decimal(prices.get('tcgplayer', '0') or '0'),
                                'price_cardkingdom': Decimal(prices.get('cardkingdom', '0') or '0'),
                                'price_cardmarket': Decimal(prices.get('cardmarket', '0') or '0'),
                            }
                        )
                        
                        if created:
                            imported += 1
                            
                    except Exception as e:
                        self.stdout.write(f'Error importing variant: {e}')
            
            if i % 1000 == 0:
                self.stdout.write(f'Imported {imported} variants so far...')
        
        self.stdout.write(self.style.SUCCESS(f'Import complete! Imported {imported} variants'))