"""Optional CRUD smoke test against configured Supabase (local or disposable project)."""
import os
import unittest
from uuid import UUID, uuid4

from app.database.client import get_supabase_client
from app.database.products import ProductRepository

ENABLED = os.getenv("RUN_SUPABASE_INTEGRATION") == "1"
HAS_CREDENTIALS = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


@unittest.skipUnless(ENABLED and HAS_CREDENTIALS, "set RUN_SUPABASE_INTEGRATION=1 and Supabase credentials")
class SupabaseCrudIntegrationTests(unittest.TestCase):
    def test_product_crud_round_trip(self):
        repository = ProductRepository(get_supabase_client())
        name = f"Phase 1 CRUD test {uuid4()}"
        product_id = None
        try:
            created = repository.create({"name": name, "category": "test"})
            product_id = created["id"]
            self.assertEqual(repository.get(UUID(product_id))["name"], name)
            updated = repository.update(UUID(product_id), {"brand": "Test Brand"})
            self.assertEqual(updated["brand"], "Test Brand")
        finally:
            if product_id:
                repository.delete(UUID(product_id))

