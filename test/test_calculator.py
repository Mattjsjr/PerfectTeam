import pytest
from calculate import build_query

build_query_input_1 = "a"
build_query_input_2 = 1
def test_build_query_rejects_non_player():
    with pytest.raises(TypeError, match=f"build_query only accepts a a JSON object containing player information. Received {build_query_input_1} instead."):
        build_query(build_query_input_1)
        build_query(build_query_input_2)

testbuild_query_rejects_invalid_dictionary_1 = {}
def testbuild_query_rejects_invalid_dictionary():
    with pytest.raises(ValueError, match=f"malformed entry for '{testbuild_query_rejects_invalid_dictionary_1}': expected a dictionary with 'selected' key"):
        build_query(testbuild_query_rejects_invalid_dictionary_1)