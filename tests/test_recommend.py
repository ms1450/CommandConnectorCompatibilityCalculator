"""
Author: Ian Young
Purpose: Test recursive logic using pytest.
"""

import pytest
from app.recommend import get_connectors


@pytest.mark.parametrize(
    "channels, storage, recommendation, expected",
    [
        (10, 5, None, ["CC300-8TB"]),  # happy_path_1
        (25, 16, None, ["CC500-16TB"]),  # happy_path_2
        (30, 20, None, ["CC700-32TB"]),  # happy_path_3
        (0, 0, None, []),  # edge_case_zero_channels_storage
        (-5, -10, None, []),  # edge_case_negative_channels_storage
        (
            10,
            5,
            ["CC300-8TB"],
            ["CC300-8TB", "CC300-8TB"],
        ),  # edge_case_existing_recommendation
        (
            100,
            100,
            None,
            ["CC700-32TB", "CC700-32TB", "CC700-32TB", "CC300-4TB"],
        ),  # edge_case_large_values
    ],
    ids=[
        "happy_path_1",
        "happy_path_2",
        "happy_path_3",
        "edge_case_zero_channels_storage",
        "edge_case_negative_channels_storage",
        "edge_case_existing_recommendation",
        "edge_case_large_values",
    ],
)
def test_get_connectors(channels, storage, recommendation, expected):
    """
    Test the get_connectors function for various scenarios.

    This function verifies that the get_connectors function returns the
    expected list of recommended connectors based on the provided
    channels, storage, and existing recommendations. It checks multiple
    cases to ensure the function behaves correctly under different
    conditions.

    Args:
        channels (int): The number of available channels required.
        storage (float): The amount of storage required.
        recommendation (Optional[List[str]]): A list of existing
            recommendations to consider.
        expected (List[str]): The expected list of recommended
            connectors.

    Returns:
        None: This function does not return a value but asserts the
            correctness of the output.
    """
    # Act
    result = get_connectors(channels, storage, recommendation)

    # Assert
    assert result == expected
