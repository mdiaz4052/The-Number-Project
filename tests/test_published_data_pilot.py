from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from Discovery.published_data_pilot import (
    CLARIFICATION_PATH,
    DEFAULT_OUTPUT,
    DOCUMENT_SPECS,
    PREREGISTRATION_PATH,
    SOURCE_AUDIT_PATH,
    build_pilot_manifest,
    load_pilot_manifest,
    serialize_artifact,
    sha256_bytes,
    validate_pilot_manifest_record,
)


class PublishedDataPilotTests(unittest.TestCase):
    def _copied_document_root(self, parent: Path) -> Path:
        root = parent / "repository"
        for source in (PREREGISTRATION_PATH, CLARIFICATION_PATH, SOURCE_AUDIT_PATH):
            destination = root / source
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        return root

    def test_clean_generated_manifest_is_current_and_deterministic(self) -> None:
        artifact = build_pilot_manifest()
        self.assertEqual(artifact, build_pilot_manifest())
        self.assertEqual(
            DEFAULT_OUTPUT.read_text(encoding="utf-8"),
            serialize_artifact(artifact),
        )
        validate_pilot_manifest_record(load_pilot_manifest())

    def test_each_governing_document_is_hash_pinned(self) -> None:
        for _, document_path, _ in DOCUMENT_SPECS:
            with self.subTest(document=document_path):
                with tempfile.TemporaryDirectory() as directory:
                    root = self._copied_document_root(Path(directory))
                    path = root / document_path
                    path.write_bytes(path.read_bytes() + b"\nChanged.\n")
                    with self.assertRaisesRegex(
                        ValueError,
                        "pinned pilot document hash mismatch",
                    ):
                        build_pilot_manifest(root)

    def test_rehashing_a_changed_preregistration_does_not_restore_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._copied_document_root(Path(directory))
            changed_path = root / PREREGISTRATION_PATH
            changed_path.write_bytes(changed_path.read_bytes() + b"\nChanged.\n")
            forged = deepcopy(load_pilot_manifest())
            changed_hash = sha256_bytes(changed_path.read_bytes())
            for document in forged["documents"]:
                if document["path"] == PREREGISTRATION_PATH.as_posix():
                    document["sha256"] = changed_hash
            with self.assertRaisesRegex(
                ValueError,
                "pinned pilot document hash mismatch",
            ):
                validate_pilot_manifest_record(forged, root=root)

    def test_semantic_manifest_fields_are_canonical(self) -> None:
        original = load_pilot_manifest()
        mutations = (
            ("decision", "GO"),
            ("outcome_class", "SUCCESSFUL_REPRODUCTION"),
            ("go_authorized", True),
            ("empirical_record_created", True),
            ("essential_missing_inputs", []),
            ("next_candidate", "algebraically_convenient_candidate"),
        )
        for field, replacement in mutations:
            with self.subTest(field=field):
                changed = json.loads(json.dumps(original))
                changed[field] = replacement
                with self.assertRaisesRegex(
                    ValueError,
                    "canonical reviewed fields",
                ):
                    validate_pilot_manifest_record(changed)

    def test_canonical_decision_and_outcome_match_pinned_audit_line(self) -> None:
        mutations = (
            ("Discovery.published_data_pilot.DECISION", "GO"),
            (
                "Discovery.published_data_pilot.OUTCOME_CLASS",
                "SUCCESSFUL_REPRODUCTION",
            ),
        )
        for target, replacement in mutations:
            with self.subTest(target=target), patch(target, replacement):
                with self.assertRaisesRegex(
                    ValueError,
                    "source-audit decision line does not match canonical decision",
                ):
                    build_pilot_manifest()


if __name__ == "__main__":
    unittest.main()
