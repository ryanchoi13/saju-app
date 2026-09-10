from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException
import main
import wardrobe_store as store


class WardrobePersistenceTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.env = patch.dict(os.environ, {"DATABASE_URL": "", "RENDER": "",
            "RENDER_SERVICE_ID": "", "DALHA_WARDROBE_DB": str(Path(self.temp.name) / "wardrobe.sqlite")})
        self.env.start()
        self.item = dict(category="시계", nickname="가죽 시계", colors=["블랙"], materials=["가죽/세무"])

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_add_edit_restart_and_last_item_delete_are_durable(self):
        saved = main.add_wardrobe(main.WardrobeItemRequest(user_id="user_owner", **self.item))["wardrobe_items"]
        item_id = saved[0]["id"]
        main.edit_wardrobe(item_id, main.WardrobeItemRequest(user_id="user_owner", **{**self.item, "nickname": "수정한 시계"}))
        root = Path(__file__).resolve().parents[2]
        # A fresh Python process has no in-memory application dictionaries.
        code = "import json, wardrobe_store; print(json.dumps(wardrobe_store.list_items('user_owner')))"
        restored = json.loads(subprocess.check_output([sys.executable, "-c", code], cwd=root, env=os.environ))
        self.assertEqual(restored[0]["nickname"], "수정한 시계")
        self.assertEqual(main.delete_wardrobe(item_id, "user_owner")["wardrobe_items"], [])
        self.assertEqual(json.loads(subprocess.check_output([sys.executable, "-c", code], cwd=root, env=os.environ)), [])

    def test_original_database_rows_load_by_kakao_account_and_keep_slashes(self):
        store.health()
        with store._connection() as (conn, pg):
            conn.execute("INSERT INTO users (id,kakao_id) VALUES (7,'legacy')")
            conn.execute("INSERT INTO wardrobe_items (user_id,category,nickname,colors,materials) VALUES (7,'시계','기존 시계','블랙,실버','가죽/세무,메탈')")
        result = store.list_items("user_legacy")
        self.assertEqual(result[0]["colors"], ["블랙", "실버"])
        self.assertEqual(result[0]["materials"], ["가죽/세무", "메탈"])
        # Login with an empty server users dictionary must not wipe stored items.
        self.assertEqual(main.auth_kakao(main.KakaoAuthRequest(kakao_id="legacy"))["wardrobe_items"], result)
        main.users_db.pop("user_legacy", None)

    def test_account_isolation_and_parallel_additions(self):
        store.mutate("user_other", "add", item=self.item)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _: store.mutate("user_owner", "add", item=self.item), range(8)))
        items = store.list_items("user_owner")
        self.assertEqual(len(items), 8)
        self.assertEqual(len({i["id"] for i in items}), 8)
        with self.assertRaises(KeyError):
            store.mutate("user_other", "edit", items[0]["id"], self.item)
        store.mutate("user_other", "delete", items[0]["id"])
        self.assertEqual(len(store.list_items("user_owner")), 8)

    def test_production_never_falls_back_to_memory_or_ephemeral_disk(self):
        with patch.dict(os.environ, {"RENDER": "true"}):
            with self.assertRaises(HTTPException) as error:
                main.add_wardrobe(main.WardrobeItemRequest(user_id="user_owner", **self.item))
            self.assertEqual(error.exception.status_code, 503)
            self.assertIsNone(main._wardrobe_response("user_owner")["wardrobe_items"])
            self.assertFalse(Path(os.environ["DALHA_WARDROBE_DB"]).exists())

    def test_failed_write_does_not_claim_success_or_remove_existing_items(self):
        saved = store.mutate("user_owner", "add", item=self.item)
        with patch.object(store, "mutate", side_effect=store.StorageUnavailable):
            with self.assertRaises(HTTPException) as error:
                main.delete_wardrobe(saved[0]["id"], "user_owner")
        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(store.list_items("user_owner"), saved)
