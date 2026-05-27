#!/usr/bin/env python3
"""Tests for provenance.clean_room (Layer 6 discipline mode)."""

import unittest

from provenance.clean_room import (
    InvocationPlan,
    list_permitted_kwargs,
    prepare_invocation,
)
from provenance.writer_pack import compile_writer_pack


class TestPrepareInvocation(unittest.TestCase):

    def setUp(self):
        self.pack = compile_writer_pack([], run_id="run_clean_room")

    def test_returns_plan_with_documented_defaults(self):
        plan = prepare_invocation(self.pack, writer_model="claude-opus-4-7")
        self.assertIsInstance(plan, InvocationPlan)
        self.assertEqual(plan.writer_model, "claude-opus-4-7")
        self.assertEqual(plan.writer_role, "clean_room_writer")
        self.assertEqual(plan.max_tokens, 4096)
        self.assertAlmostEqual(plan.temperature, 0.2)

    def test_empty_writer_model_raises(self):
        for bad in ("", "  ", "\t\n"):
            with self.subTest(model=repr(bad)):
                with self.assertRaises(ValueError):
                    prepare_invocation(self.pack, writer_model=bad)

    def test_non_writer_pack_type_raises(self):
        with self.assertRaises(TypeError):
            prepare_invocation(
                {"not": "a pack"},  # type: ignore[arg-type]
                writer_model="claude-opus-4-7",
            )

    def test_refuses_arbitrary_context_kwargs(self):
        """SPEC-L6-S001: extra context kwargs are refused at the API
        surface so process material cannot be silently threaded
        through under a 'context' or 'system_prompt' kwarg name."""
        with self.assertRaises(ValueError) as ctx:
            prepare_invocation(
                self.pack,
                writer_model="claude-opus-4-7",
                context="this is the conversation history",  # not permitted
            )
        self.assertIn("SPEC-L6-S001", str(ctx.exception))
        self.assertIn("context", str(ctx.exception))

    def test_refuses_system_prompt_kwarg(self):
        with self.assertRaises(ValueError):
            prepare_invocation(
                self.pack,
                writer_model="claude-opus-4-7",
                system_prompt="You are an assistant...",
            )

    def test_refuses_feedback_kwarg(self):
        with self.assertRaises(ValueError):
            prepare_invocation(
                self.pack,
                writer_model="claude-opus-4-7",
                feedback="Make it more commercial.",
            )

    def test_accepts_temperature_override(self):
        plan = prepare_invocation(
            self.pack,
            writer_model="claude-opus-4-7",
            temperature=0.7,
        )
        self.assertAlmostEqual(plan.temperature, 0.7)

    def test_accepts_max_tokens_override(self):
        plan = prepare_invocation(
            self.pack,
            writer_model="claude-opus-4-7",
            max_tokens=8000,
        )
        self.assertEqual(plan.max_tokens, 8000)


class TestPlanSerialisation(unittest.TestCase):

    def test_plan_to_dict_carries_pack_and_model(self):
        pack = compile_writer_pack([], run_id="run_serialise")
        plan = prepare_invocation(pack, writer_model="claude-opus-4-7")
        d = plan.to_dict()
        self.assertEqual(d["schema"], "warrantos-invocation-plan/v1")
        self.assertEqual(d["writer_model"], "claude-opus-4-7")
        self.assertEqual(d["writer_role"], "clean_room_writer")
        # Pack contents threaded through.
        self.assertEqual(d["writer_pack"]["run_id"], "run_serialise")


class TestListPermittedKwargs(unittest.TestCase):

    def test_returns_sorted_list_of_permitted_keys(self):
        keys = list_permitted_kwargs()
        self.assertIsInstance(keys, list)
        self.assertEqual(keys, sorted(keys))
        # Documented permitted keys are present.
        for k in ("writer_pack", "writer_model", "max_tokens", "temperature"):
            self.assertIn(k, keys)


if __name__ == "__main__":
    unittest.main(verbosity=2)
