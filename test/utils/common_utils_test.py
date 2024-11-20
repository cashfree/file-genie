from datetime import date
import pandas as pd
from file_genie.utils.common_utils import get_dynamic_password_based_on_time, filter_entries_by_transaction_types_list

def test_get_dynamic_password_based_on_time():
    today = date.today()
    expected_password = "{:02d}{:02d}{:04d}".format(today.day, today.month, today.year)

    result = get_dynamic_password_based_on_time()

    assert result == expected_password

def test_filter_entries_by_transaction_types_list_with_null_values():
    # Arrange
    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
    column_name = 'col1'
    filter_value_list = None
    filter_type = None

    # Act
    result = filter_entries_by_transaction_types_list(df, column_name, filter_value_list, filter_type)

    # Assert
    assert result.equals(df)

def test_filter_entries_by_transaction_types_list_with_equals_filter():
    # Arrange
    mock_df = pd.DataFrame({'col1': ['a', 'b', 'c'], 'col2': ['X', 'Y', 'Z']})
    mock_column_name = 'col1'
    mock_filter_value_list = ['a']
    mock_filter_type = 'equals'
    expected_output = pd.DataFrame({'col1': ['a'], 'col2': ['X']})

    # Act
    actual_output = filter_entries_by_transaction_types_list(mock_df, mock_column_name, mock_filter_value_list, mock_filter_type)

    # Assert
    assert actual_output.equals(expected_output)

def test_filter_entries_by_transaction_types_list_with_startswith_filter():
    # Arrange
    mock_df = pd.DataFrame({'col1': ['A', 'A', 'C'], 'col2': ['a', 'b', 'c']})
    mock_column_name = 'col1'
    mock_filter_value_list = ['A']
    mock_filter_type = 'startswith'
    expected_output = pd.DataFrame({'col1': ['A', 'A'], 'col2': ['a', 'b']})

    # Act
    actual_output = filter_entries_by_transaction_types_list(mock_df, mock_column_name, mock_filter_value_list, mock_filter_type)

    # Assert
    assert actual_output.equals(expected_output)

