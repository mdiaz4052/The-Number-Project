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


class PhysicalBridgeMetadataFormTests(unittest.TestCase):
    def test_access_date_requires_strict_iso_calendar_form(self) -> None:
        reference = codata_reference()
        invalid = (
            "zzz",
            "2026-9-01",
            "20260901",
            "2026-W36-2",
            "2026-02-30",
            "2026-13-01",
            " 2026-09-01",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "access date.*YYYY-MM-DD",
                ):
                    replace(reference, access_date=value)

    def test_valid_calendar_dates_are_accepted(self) -> None:
        reference = codata_reference()
        self.assertEqual(
            replace(reference, access_date="2024-02-29").access_date,
            "2024-02-29",
        )
        self.assertEqual(
            replace(reference, access_date="2026-09-02").access_date,
            "2026-09-02",
        )

    def test_source_identifier_requires_explicit_supported_prefix(self) -> None:
        reference = codata_reference()
        invalid = (
            "zzz",
            "ftp:example.org/data",
            "DOI:10.1063/5.0279860",
            "doi:zzz",
            "doi:10.12/example",
            "doi:10.1234/",
            "url:http://example.org/data",
            "url:https://",
            "certificate:",
            "certificate:has whitespace",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "source identifier",
                ):
                    replace(reference, source_identifier=value)

    def test_supported_source_identifier_forms_are_accepted(self) -> None:
        reference = codata_reference()
        valid = (
            "doi:10.1063/5.0279860",
            "doi:10.59161/JCGM200-2012",
            "url:https://example.org/data/v1?edition=2#table-3",
            "certificate:force-reference",
            "certificate:lab-A/run_2026-09-02",
        )
        for value in valid:
            with self.subTest(value=value):
                self.assertEqual(
                    replace(reference, source_identifier=value).source_identifier,
                    value,
                )

    def test_edition_remains_descriptive_nonempty_text(self) -> None:
        reference = codata_reference()
        descriptive = "2022 CODATA adjustment, published 2025"
        self.assertEqual(
            replace(reference, edition=descriptive).edition,
            descriptive,
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "edition.*nonempty",
        ):
            replace(reference, edition="   ")


if __name__ == "__main__":
    unittest.main()
