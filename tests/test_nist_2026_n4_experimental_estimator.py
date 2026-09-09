from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import inspect
import unittest

from Discovery import nist_2026_n4_experimental_estimator as n


EXPECTED_WEIGHTS = (
    Fraction(
        181474220273038136445997331644980427243882454968781951500875,
        293734500207598481106485362497071232997517854993839218929963,
    ),
    Fraction(
        74703562192978080723054215110332740654356494138987194012000,
        293734500207598481106485362497071232997517854993839218929963,
    ),
    Fraction(
        37211613495473325961533370812925220434050442661784089117088,
        293734500207598481106485362497071232997517854993839218929963,
    ),
    Fraction(
        345104246108937975900444928832844665228463224285984300000,
        293734500207598481106485362497071232997517854993839218929963,
    ),
)
EXPECTED_ESTIMATE = Fraction(
    980134905171160326997411014326434855394562420941209695059629104903,
    146867250103799240553242681248535616498758927496919609464981500000,
)
EXPECTED_VARIANCE = Fraction(
    3677800177239233001142779782632832550875338485270741620041938912543006237,
    183584062629749050691553351560669520623448659371149511831226875000000000000000000,
)
EXPECTED_ABSOLUTE_UNCERTAINTIES = (
    Fraction(96767809, 625000000000),
    Fraction(2022228363, 10000000000000),
    Fraction(20017911, 80000000000),
    Fraction(1566636051, 2500000000000),
)


class NIST2026N4EstimatorBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = n.verify_preregistration()
        cls.authorization = n.load_upstream_authorization(cls.protocol)
        cls.projection = cls.protocol["input_projection"]
        cls.state = n.estimator_state(cls.projection)

    def test_freeze_pins_dm073_inputs_and_bayesian_boundary(self):
        self.assertEqual(
            tuple(row["relative_standard_uncertainty_ppm"] for row in self.projection["measurements"]),
            ("23.2", "30.3", "37.5", "93.9"),
        )
        self.assertEqual(
            self.protocol["upstream_authorization"]["required_bayesian_blocker_ids"],
            [
                "epsilon_likelihood_distribution",
                "posterior_sampler_algorithm",
                "posterior_sampling_controls",
                "robust_estimator_computational_conventions",
                "dark_correlation_matrix_identity",
            ],
        )
        self.assertEqual(self.authorization["decisions"]["experimental_covariance"], "GO")
        self.assertEqual(self.authorization["decisions"]["published_bayesian_consensus"], "NO_GO")
        self.assertEqual(self.authorization["decisions"]["equation_64_reproduction"], "NOT_AUTHORIZED")
        self.assertEqual(self.authorization["decisions"]["common_constant_comparison"], "NOT_EVALUATED")

    def test_exact_absolute_uncertainties_and_covariance_definition(self):
        self.assertEqual(self.state["absolute_uncertainties"], EXPECTED_ABSOLUTE_UNCERTAINTIES)
        for i in range(4):
            self.assertEqual(
                self.state["covariance"][i][i],
                EXPECTED_ABSOLUTE_UNCERTAINTIES[i] ** 2,
            )
            for j in range(4):
                self.assertEqual(self.state["covariance"][i][j], self.state["covariance"][j][i])
                self.assertEqual(
                    self.state["covariance"][i][j],
                    self.state["correlation"][i][j]
                    * EXPECTED_ABSOLUTE_UNCERTAINTIES[i]
                    * EXPECTED_ABSOLUTE_UNCERTAINTIES[j],
                )
        self.assertTrue(all(value > 0 for value in self.state["leading_principal_minors"]))

    def test_exact_four_weights_and_unbiased_normalization(self):
        self.assertEqual(self.state["weights"], EXPECTED_WEIGHTS)
        self.assertEqual(sum(self.state["weights"]), Fraction(1))
        self.assertTrue(all(weight > 0 for weight in self.state["weights"]))
        self.assertTrue(all(weight != 0 for weight in self.state["weights"]))
        solved = n.solve_exact([list(row) for row in self.state["covariance"]], [Fraction(1)] * 4)
        self.assertEqual(
            tuple(value / sum(solved) for value in solved),
            EXPECTED_WEIGHTS,
        )

    def test_exact_point_estimate_and_variance_identities(self):
        self.assertEqual(self.state["estimate"], EXPECTED_ESTIMATE)
        self.assertEqual(self.state["variance"], EXPECTED_VARIANCE)
        self.assertEqual(
            self.state["estimate"],
            sum(weight * value for weight, value in zip(self.state["weights"], self.state["values"])),
        )
        quadratic = sum(
            self.state["weights"][i]
            * sum(
                self.state["covariance"][i][j] * self.state["weights"][j]
                for j in range(4)
            )
            for i in range(4)
        )
        self.assertEqual(self.state["variance"], quadratic)
        self.assertEqual(self.state["variance"], Fraction(1, 1) / self.state["normalization"])

    def test_real_finite_resolution_enclosure_is_exact(self):
        half = Fraction(1, 2_000_000)
        self.assertEqual(
            self.state["aggregate_enclosure"],
            (EXPECTED_ESTIMATE - half, EXPECTED_ESTIMATE + half),
        )
        self.assertEqual(
            self.state["aggregate_enclosure"][1] - self.state["aggregate_enclosure"][0],
            Fraction(1, 1_000_000),
        )
        for value, cell in zip(self.state["values"], self.state["input_cells"]):
            self.assertEqual(cell, (value - half, value + half))

    def test_signed_weight_enclosure_helper_uses_correct_extrema(self):
        cells = ((Fraction(0), Fraction(2)), (Fraction(10), Fraction(14)))
        weights = (Fraction(3, 2), Fraction(-1, 2))
        self.assertEqual(n.linear_enclosure(cells, weights), (Fraction(-7), Fraction(-2)))

    def test_off_diagonal_correlations_are_load_bearing(self):
        changed = deepcopy(self.projection)
        for i in range(4):
            for j in range(4):
                changed["correlation_matrix"][i][j] = "1" if i == j else "0"
        independent = n.estimator_state(changed)
        self.assertNotEqual(independent["weights"], self.state["weights"])
        self.assertNotEqual(independent["estimate"], self.state["estimate"])
        self.assertNotEqual(independent["variance"], self.state["variance"])

    def test_table18_precision_is_load_bearing(self):
        changed = deepcopy(self.projection)
        rounded = ("23", "30", "38", "94")
        for row, uncertainty in zip(changed["measurements"], rounded):
            row["relative_standard_uncertainty_ppm"] = uncertainty
        rounded_state = n.estimator_state(changed)
        self.assertNotEqual(rounded_state["weights"], self.state["weights"])
        self.assertNotEqual(rounded_state["estimate"], self.state["estimate"])

    def test_absolute_covariance_scaling_is_load_bearing(self):
        relative = []
        for i in range(4):
            row = []
            for j in range(4):
                row.append(
                    self.state["correlation"][i][j]
                    * self.state["relative_uncertainties_ppm"][i]
                    * self.state["relative_uncertainties_ppm"][j]
                )
            relative.append(row)
        solution = n.solve_exact(relative, [Fraction(1)] * 4)
        relative_weights = tuple(value / sum(solution) for value in solution)
        self.assertNotEqual(relative_weights, self.state["weights"])

    def test_all_four_values_are_load_bearing(self):
        for index in range(4):
            changed = deepcopy(self.projection)
            value = n.decimal_fraction(changed["measurements"][index]["G_decimal_in_1e_minus_11_units"])
            changed["measurements"][index]["G_decimal_in_1e_minus_11_units"] = n._decimal_text(
                value + Fraction(1, 1_000_000), 6
            )
            changed_state = n.estimator_state(changed)
            self.assertNotEqual(changed_state["estimate"], self.state["estimate"])

    def test_estimator_api_excludes_bayesian_and_bipm_fields(self):
        self.assertEqual(tuple(inspect.signature(n.estimator_state).parameters), ("input_projection",))
        source = inspect.getsource(n.estimator_state)
        for forbidden in ("equation_64", "Table 19", "CODATA", "BIPM", "dark_uncertainty"):
            self.assertNotIn(forbidden, source)

    def test_invalid_projection_and_covariance_fail_closed(self):
        reordered = deepcopy(self.projection)
        reordered["measurements"][0], reordered["measurements"][1] = (
            reordered["measurements"][1], reordered["measurements"][0]
        )
        with self.assertRaises(n.NISTN4EstimatorError):
            n.estimator_state(reordered)

        asymmetric = deepcopy(self.projection)
        asymmetric["correlation_matrix"][0][1] = "0.41"
        with self.assertRaises(n.NISTN4EstimatorError):
            n.estimator_state(asymmetric)

        singular = deepcopy(self.projection)
        singular["correlation_matrix"] = [["1"] * 4 for _ in range(4)]
        with self.assertRaises(n.NISTN4EstimatorError):
            n.estimator_state(singular)

        bad_precision = deepcopy(self.projection)
        bad_precision["measurements"][0]["printed_decimal_places"] = 5
        with self.assertRaises(n.NISTN4EstimatorError):
            n.estimator_state(bad_precision)

    def test_upstream_authorization_mutations_fail_closed(self):
        feasibility = n._json((n.ROOT / n.UPSTREAM_FEASIBILITY_PATH).read_bytes())
        attestation = n._json((n.ROOT / n.UPSTREAM_ATTESTATION_PATH).read_bytes())

        changed = deepcopy(feasibility)
        changed["decision"]["equation_64_reproduction"] = "AUTHORIZED"
        with self.assertRaises(n.NISTN4EstimatorError):
            n.validate_upstream_records(self.protocol, changed, attestation)

        changed = deepcopy(feasibility)
        changed["published_bayesian_consensus_layer"]["missing_result_driving_information"].pop()
        with self.assertRaises(n.NISTN4EstimatorError):
            n.validate_upstream_records(self.protocol, changed, attestation)

        changed_attestation = deepcopy(attestation)
        changed_attestation["experimental_layer"]["table_18"]["diagonal_relative_standard_uncertainty_ppm"][0] = "23.3"
        with self.assertRaises(n.NISTN4EstimatorError):
            n.validate_upstream_records(self.protocol, feasibility, changed_attestation)


class NIST2026N4EstimatorArtifactTests(unittest.TestCase):
    def test_preregistration_anchor_and_read_closure_prerequisite_chronology(self):
        protocol = n.verify_preregistration()
        self.assertEqual(protocol["intended_base_sha"], n.BASELINE)
        n.verify_implementation_chronology()

    def test_source_inventory_is_bounded_and_nist_scoped(self):
        self.assertIn(n.READ_CLOSURE_TEST_PATH, n.SOURCE_PATHS)
        self.assertTrue(all("hust_2018" not in path.lower() for path in n.SOURCE_PATHS))
        self.assertTrue(all("schlamminger_2006" not in path.lower() for path in n.SOURCE_PATHS))
        self.assertTrue(all("newman_2014" not in path.lower() for path in n.SOURCE_PATHS))

    def test_committed_artifact_matches_rebuild(self):
        path = n.ROOT / n.DEFAULT_OUTPUT
        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(), n.serialize_artifact(n.build_artifact()))


if __name__ == "__main__":
    unittest.main()
