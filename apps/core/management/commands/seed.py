from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed de dados sintéticos (implementação rica na Fase 5)."

    def handle(self, *args, **options) -> None:
        self.stdout.write(
            self.style.WARNING("seed: noop nesta fase — dados ricos entram na Fase 5 (OpenAPI/DX).")
        )
