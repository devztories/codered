from django.core.management.base import BaseCommand
from django.db import connection
from orders.models import Order

class Command(BaseCommand):
    help = "Add the project tracking stage column to an existing orders table if it is missing."

    def handle(self, *args, **options):
        table = Order._meta.db_table
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            if table not in tables:
                self.stdout.write(self.style.WARNING("Orders table does not exist yet; run migrate --run-syncdb first."))
                return
            columns = {c.name for c in connection.introspection.get_table_description(cursor, table)}
        if 'stage' in columns:
            self.stdout.write(self.style.SUCCESS("Project tracking stage is already installed."))
            return
        field = Order._meta.get_field('stage')
        with connection.schema_editor() as editor:
            editor.add_field(Order, field)
        self.stdout.write(self.style.SUCCESS("Added project tracking stage. Existing orders start at Project Discussed."))
