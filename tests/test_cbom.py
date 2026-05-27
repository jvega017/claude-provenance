#!/usr/bin/env python3
"""Tests for provenance.cbom."""

import json
import unittest

from provenance.cbom import (
    CBOM,
    ClaimRecord,
    ContextInput,
    ReviewFindingRecord,
    TransformationRecord,
    build_cbom,
)


class TestCbomBuild(unittest.TestCase):

    def test_cbom_represents_inputs_transformations_material_claims_and_findings(self):
        cbom = build_cbom(
            context_inputs=[
                ContextInput(
                    context_id="ctx_source",
                    text="Official report page 4.",
                    source="report.pdf",
                    material_type="source",
                ),
                ContextInput(
                    context_id="ctx_sensitive",
                    text="Private drafting notes.",
                    source="session",
                    material_type="process",
                    admitted=False,
                    reason="process material cannot appear in final prose",
                ),
            ],
            transformations=[
                TransformationRecord(
                    transform_id="tx_001",
                    input_ids=["ctx_source"],
                    output_id="claim_001",
                    kind="extract_claim",
                    description="Converted source paragraph into a factual claim.",
                )
            ],
            claims=[
                ClaimRecord(
                    claim_id="claim_001",
                    text="The programme reduced costs by 12 per cent.",
                    support_ids=["ctx_source"],
                    status="supported",
                )
            ],
            review_findings=[
                ReviewFindingRecord(
                    finding_id="f_001",
                    severity="P1",
                    title="Unsupported comparator",
                    disposition="distinct",
                )
            ],
            artefact_id="draft_7",
        )

        data = cbom.to_dict()

        self.assertEqual(data["schema"], "warrantos-cbom/v1")
        self.assertEqual(data["artefact_id"], "draft_7")
        self.assertEqual(data["summary"]["context_inputs"], 2)
        self.assertEqual(data["summary"]["admitted_material"], 1)
        self.assertEqual(data["summary"]["blocked_material"], 1)
        self.assertEqual(data["summary"]["claims"], 1)
        self.assertEqual(data["summary"]["review_findings"], 1)
        self.assertEqual(data["blocked_material"][0]["context_id"], "ctx_sensitive")
        self.assertEqual(data["admitted_material"][0]["context_id"], "ctx_source")
        json.dumps(data)

    def test_empty_cbom_has_stable_shape(self):
        cbom = build_cbom()
        data = cbom.to_dict()

        self.assertIsInstance(cbom, CBOM)
        self.assertEqual(data["summary"]["context_inputs"], 0)
        self.assertEqual(data["context_inputs"], [])
        self.assertEqual(data["transformations"], [])
        self.assertEqual(data["claims"], [])
        self.assertEqual(data["review_findings"], [])


class TestCbomValidation(unittest.TestCase):

    def test_transformation_input_ids_must_reference_context_inputs(self):
        with self.assertRaises(ValueError):
            build_cbom(
                context_inputs=[ContextInput("ctx_001", "Source text.")],
                transformations=[
                    TransformationRecord(
                        transform_id="tx_bad",
                        input_ids=["missing"],
                        output_id="claim_001",
                        kind="extract_claim",
                        description="Bad reference.",
                    )
                ],
            )

    def test_claim_support_ids_must_reference_admitted_inputs(self):
        with self.assertRaises(ValueError):
            build_cbom(
                context_inputs=[
                    ContextInput(
                        context_id="ctx_blocked",
                        text="Private notes.",
                        admitted=False,
                    )
                ],
                claims=[
                    ClaimRecord(
                        claim_id="claim_001",
                        text="A derived claim.",
                        support_ids=["ctx_blocked"],
                    )
                ],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
