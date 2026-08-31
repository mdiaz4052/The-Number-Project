import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from Discovery.falsification_preregistration import (
    DEFAULT_OUTPUT,
    EXPERIMENT_IDENTIFIER,
    IMPLEMENTATION_BASE_SHA,
    PREREGISTRATION_SCHEMA_VERSION,
    build_preregistration,
    load_preregistration,
    main,
    preregistration_sha256_bytes,
    serialize_artifact,
    validate_preregistration_record,
)


class FalsificationPreregistrationTests(unittest.TestCase):
    def test_committed_preregistration_is_deterministic_and_current(self) -> None:
        first = serialize_artifact(build_preregistration())
        second = serialize_artifact(build_preregistration())
        self.assertEqual(first, second)
        self.assertEqual(DEFAULT_OUTPUT.read_text(encoding="utf-8"), first)
        self.assertTrue(first.endswith("\n"))

    def test_hash_matches_exact_committed_bytes(self) -> None:
        record, content = load_preregistration()
        self.assertEqual(record["experiment_identifier"], EXPERIMENT_IDENTIFIER)
        self.assertEqual(len(preregistration_sha256_bytes(content)), 64)
        changed = content + b" "
        self.assertNotEqual(
            preregistration_sha256_bytes(content),
            preregistration_sha256_bytes(changed),
        )

    def test_stale_version_is_rejected(self) -> None:
        record = build_preregistration()
        record["preregistration_schema_version"] = PREREGISTRATION_SCHEMA_VERSION + 1
        with self.assertRaisesRegex(ValueError, "stale preregistration schema"):
            validate_preregistration_record(record)

    def test_source_sha_is_frozen_and_validated(self) -> None:
        record = build_preregistration()
        self.assertEqual(
            record["repository"]["source_commit_sha"], IMPLEMENTATION_BASE_SHA
        )
        record["repository"]["source_commit_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source commit SHA mismatch"):
            validate_preregistration_record(record)

    def test_seeds_are_frozen_and_survive_round_trip(self) -> None:
        record = build_preregistration()
        seeds = record["randomness"]["seeds"]
        reparsed = json.loads(serialize_artifact(record))
        self.assertEqual(reparsed["randomness"]["seeds"], seeds)
        self.assertEqual(set(seeds), {"local_null", "global_null"})

    def test_check_rejects_mismatch_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preregistration.json"
            path.write_text("{}\n", encoding="utf-8")
            with patch(
                "sys.argv",
                ["falsification_preregistration", "--check", "--output", str(path)],
            ):
                with self.assertRaises(SystemExit):
                    main()
            self.assertEqual(path.read_text(encoding="utf-8"), "{}\n")

    def test_regeneration_refuses_to_overwrite_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preregistration.json"
            path.write_text("{}\n", encoding="utf-8")
            with patch(
                "sys.argv",
                ["falsification_preregistration", "--output", str(path)],
            ):
                with self.assertRaises(SystemExit):
                    main()
            self.assertEqual(path.read_text(encoding="utf-8"), "{}\n")


if __name__ == "__main__":
    unittest.main()
