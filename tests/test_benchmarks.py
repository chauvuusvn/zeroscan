#!/usr/bin/env python3
"""
Unit tests for Zero-Scan Benchmark Suite (benchmarks/evaluator.py).
"""

import unittest
from benchmarks.evaluator import generate_markdown_report, run_benchmark_evaluation


class TestBenchmarkEvaluator(unittest.TestCase):
    def test_run_benchmark_evaluation(self):
        data = run_benchmark_evaluation()
        self.assertIn("average_token_reduction_pct", data)
        self.assertIn("tiers", data)
        self.assertGreater(data["average_token_reduction_pct"], 90.0)
        self.assertEqual(len(data["tiers"]), 5)

    def test_generate_markdown_report(self):
        data = run_benchmark_evaluation()
        report = generate_markdown_report(data)
        self.assertIn("Zero-Scan Context Efficiency", report)
        self.assertIn("Average Token Reduction", report)
        self.assertIn("Quantitative Comparison Matrix", report)


if __name__ == "__main__":
    unittest.main()
