from dataclasses import replace
import unittest

from Discovery.physical_bridge import (
    BridgeValidationError,
    build_inverse_square_model,
)


def codata_reference():
    model = build_inverse_square_model()
    return next(
        quantity
        for quantity in model.quantities
        if quantity.identifier == "codata_2022_G"
    )


def force_reference():
    model = build_inverse_square_model()
    return next(
        quantity
        for quantity in model.quantities
        if quantity.identifier == "force_reference"
    )


class PhysicalBridgeSourceIdentifierHardeningTests(unittest.TestCase):
    def test_certificate_identifier_requires_namespaced_issuer_and_record(self) -> None:
        reference = codata_reference()
        invalid = (
            "certificate:zzz",
            "certificate:force-reference",
            "certificate:http://not-https.example/x",
            "certificate:10.12/too-short-registrant",
            "certificate:doi:10.12/x",
            "certificate:/record",
            "certificate:lab-A/",
            "certificate:lab-A/run/extra",
            "certificate:lab-A/rec:x",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "certificate.*issuer/record",
                ):
                    replace(reference, source_identifier=value)

        valid = (
            "certificate:project/force-reference",
            "certificate:lab-A/run_2026-09-02",
            "certificate:NIST/calibration-2026.0042",
        )
        for value in valid:
            with self.subTest(value=value):
                self.assertEqual(
                    replace(reference, source_identifier=value).source_identifier,
                    value,
                )

        issuer_64 = "A" + "a" * 63
        record_128 = "r" * 128
        for value in (
            f"certificate:{issuer_64}/record",
            f"certificate:lab/{record_128}",
        ):
            with self.subTest(boundary=value):
                self.assertEqual(
                    replace(reference, source_identifier=value).source_identifier,
                    value,
                )
        for value in (
            f"certificate:{issuer_64}a/record",
            f"certificate:lab/{record_128}r",
        ):
            with self.subTest(over_bound=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "certificate.*issuer/record",
                ):
                    replace(reference, source_identifier=value)

    def test_legacy_force_reference_token_is_rejected_without_migration_shim(self) -> None:
        for reference in (force_reference(), codata_reference()):
            with self.subTest(identifier=reference.identifier):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "certificate.*issuer/record",
                ):
                    replace(
                        reference,
                        source_identifier="certificate:force-reference",
                    )

        with self.assertRaisesRegex(
            BridgeValidationError,
            "certificate.*issuer/record",
        ):
            replace(
                force_reference(),
                source_identifier="certificate:zzz",
            )

    def test_https_credentials_are_rejected(self) -> None:
        reference = codata_reference()
        for value in (
            "url:https://user:pass@example.org/data",
            "url:https://user@example.org/data",
            "url:https://:pass@example.org/data",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "credential-free https URL",
                ):
                    replace(reference, source_identifier=value)

    def test_invisible_or_control_identifier_characters_are_rejected(self) -> None:
        reference = codata_reference()
        invalid = (
            "doi:10.1103/x\u00a0y",
            "doi:10.1103/x\u200by",
            "doi:10.1103/x\x01y",
            "doi:10.1103/x\u115fy",
            "doi:10.1103/x\u2800y",
            "doi:10.1103/x\u3164y",
            "doi:10.1103/x\uffa0y",
            "url:https://ex\u3164ample.org/d",
            "url:https://example.org/x\u200by",
        )
        for value in invalid:
            with self.subTest(value=repr(value)):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "whitespace, control, or invisible",
                ):
                    replace(reference, source_identifier=value)

        unicode_doi = "doi:10.1234/café"
        self.assertEqual(
            replace(reference, source_identifier=unicode_doi).source_identifier,
            unicode_doi,
        )

    def test_non_nfc_identifier_is_rejected_instead_of_rewritten(self) -> None:
        reference = codata_reference()
        decomposed = "doi:10.1234/cafe\u0301"
        composed = "doi:10.1234/café"
        self.assertNotEqual(decomposed, composed)
        with self.assertRaisesRegex(
            BridgeValidationError,
            "source identifier.*must be NFC-normalized",
        ):
            replace(reference, source_identifier=decomposed)
        self.assertEqual(
            replace(reference, source_identifier=composed).source_identifier,
            composed,
        )

    def test_ascii_space_rejection_is_independently_pinned_for_urls(self) -> None:
        reference = codata_reference()
        for value in (
            "url:https://example.org/a b",
            "url:https://exam ple.org/d",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "whitespace, control, or invisible",
                ):
                    replace(reference, source_identifier=value)

    def test_unparseable_urls_use_bridge_validation_error(self) -> None:
        reference = codata_reference()
        invalid = (
            "url:https://[::1/d",
            "url:https://exa＃mple.org/d",
            "url:https://exa／mple.org/d",
            "url:https://exa＠mple.org/d",
            "url:https://exa：mple.org/d",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "URL is unparseable",
                ):
                    replace(reference, source_identifier=value)

    def test_invalid_ports_and_degenerate_hosts_are_rejected(self) -> None:
        reference = codata_reference()
        for value in (
            "url:https://example.org:notaport/d",
            "url:https://example.org:99999999/d",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "URL is unparseable",
                ):
                    replace(reference, source_identifier=value)

        for value in (
            "url:https://../d",
            "url:https://.../",
            "url:https://...:1/d",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "credential-free https URL",
                ):
                    replace(reference, source_identifier=value)

    def test_future_date_and_in_memory_mutability_remain_outside_this_form_gate(self) -> None:
        reference = codata_reference()
        self.assertEqual(
            replace(reference, access_date="9999-12-31").access_date,
            "9999-12-31",
        )


if __name__ == "__main__":
    unittest.main()
