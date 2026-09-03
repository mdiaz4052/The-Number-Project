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

    def test_legacy_force_reference_token_is_scoped_and_canonicalized(self) -> None:
        migrated = replace(
            force_reference(),
            source_identifier="certificate:force-reference",
        )
        self.assertEqual(
            migrated.source_identifier,
            "certificate:project/force-reference",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "certificate.*issuer/record",
        ):
            replace(
                codata_reference(),
                source_identifier="certificate:force-reference",
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
