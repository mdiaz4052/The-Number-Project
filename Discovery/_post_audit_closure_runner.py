from pathlib import Path


def main() -> None:
    schema = Path("Discovery/physical_bridge_schema.py")
    text = schema.read_text(encoding="utf-8")
    if "import unicodedata\n" not in text:
        text = text.replace("import re\n", "import re\nimport unicodedata\n", 1)
    marker = '_SOURCE_IDENTIFIER_PREFIXES = ("doi", "url", "certificate")\n'
    insertion = '''_SOURCE_IDENTIFIER_PREFIXES = ("doi", "url", "certificate")
_INVISIBLE_SOURCE_IDENTIFIER_CHARACTERS = frozenset(
    {"\\u115f", "\\u1160", "\\u2800", "\\u3164", "\\uffa0"}
)


def _source_identifier_character_is_disallowed(character: str) -> bool:
    return (
        character.isspace()
        or not character.isprintable()
        or unicodedata.category(character) in {"Cf", "Mn"}
        or character in _INVISIBLE_SOURCE_IDENTIFIER_CHARACTERS
    )
'''
    if text.count(marker) != 1:
        raise SystemExit("schema prefix marker missing")
    text = text.replace(marker, insertion, 1)
    old_precheck = '''    if text != text.strip() or any(
        character.isspace() or not character.isprintable()
        for character in text
    ):
'''
    new_precheck = '''    if text != text.strip() or any(
        _source_identifier_character_is_disallowed(character)
        for character in text
    ):
'''
    if text.count(old_precheck) != 1:
        raise SystemExit("schema precheck marker missing")
    text = text.replace(old_precheck, new_precheck, 1)
    shim = '''        source_identifier = self.source_identifier
        if (
            self.identifier == "force_reference"
            and source_identifier == "certificate:force-reference"
        ):
            source_identifier = "certificate:project/force-reference"
            object.__setattr__(self, "source_identifier", source_identifier)
        if source_identifier is not None:
            _validate_source_identifier(
                source_identifier,
'''
    replacement = '''        source_identifier = self.source_identifier
        if source_identifier is not None:
            _validate_source_identifier(
                source_identifier,
'''
    if text.count(shim) != 1:
        raise SystemExit("legacy shim marker missing")
    text = text.replace(shim, replacement, 1)
    text = text.replace("    return text\n\ndef _unique_text", "    return text\n\n\ndef _unique_text", 1)
    schema.write_text(text, encoding="utf-8")

    bridge_tests = Path("tests/test_physical_bridge.py")
    bridge_text = bridge_tests.read_text(encoding="utf-8")
    count = bridge_text.count("certificate:force-reference")
    if count != 2:
        raise SystemExit(f"expected two legacy fixture literals, found {count}")
    bridge_tests.write_text(
        bridge_text.replace(
            "certificate:force-reference", "certificate:project/force-reference"
        ),
        encoding="utf-8",
    )

    hardening = r'''from dataclasses import replace
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
'''
    Path("tests/test_physical_bridge_source_identifier_hardening.py").write_text(
        hardening, encoding="utf-8"
    )

    harness = Path("Discovery/mutation_harness.py")
    h = harness.read_text(encoding="utf-8")
    if h.count("RESULT_SCHEMA_VERSION = 3") != 1:
        raise SystemExit("mutation result schema marker missing")
    h = h.replace("RESULT_SCHEMA_VERSION = 3", "RESULT_SCHEMA_VERSION = 4", 1)
    old_output = '"Experiments/Falsification/milestone_5b_core_v1.mutation_results.json"'
    if h.count(old_output) != 1:
        raise SystemExit("mutation output marker missing")
    h = h.replace(
        old_output,
        '"Experiments/Falsification/milestone_5b_core_v1.mutation_results_v2.json"',
        1,
    )
    source_marker = '    "Discovery/physical_bridge_validation.py",\n'
    if h.count(source_marker) != 1:
        raise SystemExit("mutation SOURCE_PATHS marker missing")
    h = h.replace(
        source_marker,
        '    "Discovery/physical_bridge_schema.py",\n' + source_marker,
        1,
    )
    harness.write_text(h, encoding="utf-8")

    mutation_tests = Path("tests/test_mutation_harness.py")
    mt = mutation_tests.read_text(encoding="utf-8")
    if mt.count('"result_schema_version": 3,') != 1:
        raise SystemExit("mutation schema-version fixture marker missing")
    mutation_tests.write_text(
        mt.replace('"result_schema_version": 3,', '"result_schema_version": 4,', 1),
        encoding="utf-8",
    )

    readme = Path("Experiments/GMeasurements/README.md")
    r = readme.read_text(encoding="utf-8")
    old_meta = '''DOI and URL identifiers reject whitespace, control,
and invisible characters; malformed URL parsing and invalid ports are converted into the
schema's controlled `BridgeValidationError`. Edition remains descriptive nonempty text.
Malformed forms are rejected before model-level empirical evaluation.

One historical source-attested test fixture predates the certificate namespace and uses
the exact token `certificate:force-reference`. For the repository's known
`force_reference` quantity only, construction canonicalizes that token to
`certificate:project/force-reference`; the same loose token remains invalid for every
other quantity. This is a migration shim for preserved historical tests, not an additional
accepted certificate grammar.
'''
    new_meta = '''DOI and URL identifiers reject whitespace, control, non-printable characters, Unicode
format/combining-mark categories, and a bounded set of known visually blank filler
characters; malformed URL parsing and invalid ports are converted into the schema's
controlled `BridgeValidationError`. Printable Unicode letters remain allowed in DOI
suffixes, but general Unicode homoglyph/confusable detection is explicitly out of scope.
Edition remains descriptive nonempty text. Malformed forms are rejected before model-level
empirical evaluation.

The temporary `force_reference` legacy-certificate canonicalization has been retired. The
post-audit closure legitimately re-anchors the mutation-harness source boundary to include
`Discovery/physical_bridge_schema.py`, updates the two historical fixture literals to the
normal `certificate:project/force-reference` form, and writes a new mutation-results v2
artifact. The original mutation-results artifact remains preserved as historical evidence.
'''
    if r.count(old_meta) != 1:
        raise SystemExit("README metadata paragraph marker missing")
    r = r.replace(old_meta, new_meta, 1)
    locator = (
        "The proposed 2002 PRD companion citation is unrelated; the later UW correction\n"
        "identified by CODATA is sourced to a private communication."
    )
    corrected = locator + (
        " Primary NIST RMP verification places the\n"
        "correction discussion on journal p. 45 and the private-communication bibliography entry on\n"
        "journal p. 102. The manifest-pinned v1 source-audit text retains its earlier p. 44/p. 101\n"
        "locator typo and is not rewritten retroactively."
    )
    if r.count(locator) != 1:
        raise SystemExit("README RMP locator marker missing")
    readme.write_text(r.replace(locator, corrected, 1), encoding="utf-8")

    literature = Path("Notes/GMeasurementLiterature.md")
    lit = literature.read_text(encoding="utf-8")
    old_lit = '''records the
later UW correction as originating in a 2002 private communication. It is therefore
historical comparison evidence, not a public companion input set.'''
    new_lit = '''records the later UW magnetic-damper correction on journal p. 45 and lists
“Gundlach and Merkowitz, 2002” as a private communication in the bibliography on journal
p. 102. It is therefore historical comparison evidence, not a public companion input set.
The older manifest-pinned UW source-audit v1 retains p. 44/p. 101 as a historical locator
typo; that frozen audit is not rewritten.'''
    if lit.count(old_lit) != 1:
        raise SystemExit("literature RMP locator marker missing")
    literature.write_text(lit.replace(old_lit, new_lit, 1), encoding="utf-8")


if __name__ == "__main__":
    main()
