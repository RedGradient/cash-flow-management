from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "transactions"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from transactions.seed import seed_database

        def run_seed(sender, **kwargs):
            seed_database()

        post_migrate.connect(
            run_seed, sender=self, dispatch_uid="transactions_seed_data"
        )
