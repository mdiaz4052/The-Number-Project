import unittest

from Explorations.LanyonSpecAudit import audit


class LanyonSpecAuditTests(unittest.TestCase):
    def test_pins_and_edits_apply(self):
        audit.check()

    def test_mutant_inventory(self):
        mutants = audit.all_mutants()
        self.assertEqual(len([m for m in mutants if m.family == "curated"]), 14)
        self.assertEqual(len([m for m in mutants if m.family.startswith("systematic")]), 20)
        for m in mutants:
            self.assertIn(m.predicted_lanyon, ("pass", "fail"))
            self.assertIn(m.predicted_strengthened, ("pass", "fail"))

    def test_every_mutant_changes_the_spec(self):
        for m in audit.all_mutants():
            if m.edits:
                original = audit.upstream_text(m.system)
                self.assertNotEqual(audit.apply_edits(original, m.edits, m.id), original, m.id)

    def test_edit_count_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            audit.apply_edits("a a", (audit.Edit("a", "b", 1),), "X")

    def test_attribution_uses_enclosing_declaration(self):
        text = "def f := 1\n\ntheorem t : True := by\n  trivial\n"
        starts = audit.declaration_starts(text)
        self.assertEqual(audit.attribute(4, starts), ("theorem", "t"))
        self.assertEqual(audit.attribute(1, starts), ("def", "f"))

    def test_qualified_theorem_names_follow_namespaces(self):
        text = "namespace a\ntheorem t : True := trivial\nend a\ntheorem u : True := trivial\n"
        self.assertEqual(audit.qualified_theorems(text), [("t", "a.t"), ("u", "u")])


if __name__ == "__main__":
    unittest.main()
