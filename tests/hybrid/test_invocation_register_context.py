

from hybrid.invocation_register_context import reduce_for_field_insensitivity
from tests.sample_results import get_mock_invocation_register_context


def test_reduce_for_field_insensitivity():
    contexts = []

    contexts.append(get_mock_invocation_register_context(access_path="a"))
    contexts.append(get_mock_invocation_register_context(access_path="b"))
    contexts.append(get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, access_path="a"))
    contexts.append(get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, access_path="b"))
    contexts.append(get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=1, access_path="a"))
    contexts.append(get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=1, access_path="b"))
    contexts.append(get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=1, access_path="b"))

    reduced_contexts, _ = reduce_for_field_insensitivity(contexts, string_sets=[set(), set("a"), set("b"), set(["c", "d"]), set(), set(), set()])

    assert len(reduced_contexts) == 3

    assert len(reduced_contexts[0][1].fields) == 1