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

    def test_legacy_shim_is_retired_and_force_reference_gets_no_value_bypass(self) -> None:
        reference = force_reference()
        for value in ("certificate:force-reference", "certificate:zzz"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "certificate.*issuer/record",
                ):
                    replace(reference, source_identifier=value)
        valid = "certificate:evil/token"
        self.assertEqual(
            replace(reference, source_identifier=valid).source_identifier,
            valid,
        )

    def test_certificate_component_length_boundaries_are_pinned(self) -> None:
        reference = codata_reference()
        issuer_64 = "A" + "a" * 63
        record_128 = "r" * 128
        self.assertEqual(
            replace(reference, source_identifier=f"certificate:{issuer_64}/x").source_identifier,
            f"certificate:{issuer_64}/x",
        )
        self.assertEqual(
            replace(reference, source_identifier=f"certificate:A/{record_128}").source_identifier,
            f"certificate:A/{record_128}",
        )
        for value in (
            f"certificate:{'A' + 'a' * 64}/x",
            f"certificate:A/{'r' * 129}",
        ):
            with self.subTest(value=value[:40]):
                with self.assertRaisesRegex(
                    BridgeValidationError, "certificate.*issuer/record"
                ):
                    replace(reference, source_identifier=value)

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

    def test_whitespace_precheck_is_independently_pinned_for_urls(self) -> None:
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

    def test_invisible_or_control_identifier_characters_are_rejected(self) -> None:
        reference = codata_reference()
        invalid = (
            "doi:10.1103/x\u00a0y",
            "doi:10.1103/x\u200by",
            "doi:10.1103/x\x01y",
            "doi:10.1103/x\u3164y",
            "doi:10.1103/x\u2800y",
            "doi:10.1103/x\u115fy",
            "doi:10.1103/cafe\u0301",
            "url:https://ex\u3164ample.org/d",
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
