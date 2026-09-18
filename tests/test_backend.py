import unittest

import torch

from src.backend.db import vector_literal
from src.backend.ml import FashionModels
from src.jobs.index_catalog import plan_records


class BackendUtilityTest(unittest.TestCase):
    def test_vector_literal(self):
        self.assertEqual("[0.10000000,-0.25000000]", vector_literal([0.1, -0.25]))

    def test_transformers_feature_output_compatibility_shape(self):
        class Output:
            pooler_output = torch.ones((2, 512))

        output = Output()
        features = output if isinstance(output, torch.Tensor) else output.pooler_output
        self.assertEqual((2, 512), tuple(features.shape))

    def test_target_count_only_plans_missing_records(self):
        records = [
            {"product": {"goods_no": str(goods_no)}}
            for goods_no in range(1, 6)
        ]
        planned = plan_records(
            records, {"1", "4"}, limit=None, target_count=4, skip_existing=True
        )
        self.assertEqual(["2", "3"], [row["product"]["goods_no"] for row in planned])

    def test_skip_existing_limit_applies_to_new_records(self):
        records = [
            {"product": {"goods_no": str(goods_no)}}
            for goods_no in range(1, 6)
        ]
        planned = plan_records(
            records, {"1"}, limit=2, target_count=None, skip_existing=True
        )
        self.assertEqual(["2", "3"], [row["product"]["goods_no"] for row in planned])


if __name__ == "__main__":
    unittest.main()
