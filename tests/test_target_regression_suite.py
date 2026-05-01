from __future__ import annotations

import unittest


class TargetRegressionSuiteSmokeTest(unittest.TestCase):
    def test_phase1_and_phase2_target_suite_is_declared(self) -> None:
        phase1_and_2_tests = [
            "tests/test_target_build.py",
            "tests/test_rag_target.py",
            "tests/test_sft_target.py",
            "tests/test_eval_target.py",
            "tests/test_pretrain_target.py",
            "tests/test_preference_target.py",
            "tests/test_target_policy.py",
            "tests/test_entity_linking.py",
            "tests/test_target_scoring.py",
            "tests/test_source_governance.py",
            "tests/test_transform_extension.py",
        ]
        self.assertGreaterEqual(len(phase1_and_2_tests), 11)


if __name__ == "__main__":
    unittest.main()
