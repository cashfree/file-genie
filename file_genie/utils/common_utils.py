import pandas as pd
from datetime import date
from ..exceptions.expcetion import FileProcessFailException 
from ..enums.FilterType import FilterType

def get_dynamic_password_based_on_time():
        try:
            today = date.today()
            dynamic_password = "{:02d}{:02d}{:04d}".format(today.day, today.month, today.year)

            return dynamic_password
        except Exception as e:
            raise FileProcessFailException(
                  "Exception Occurred while getting dynamic password:: "+str(e))
        
def filter_entries_by_transaction_types_list(df, column_name, filter_value_list, filter_type):
    if filter_value_list is None or filter_type is None:
        return df
    filtered_df = pd.DataFrame({})
    for filter_value in filter_value_list:
        if filter_type == FilterType.EQUALS.value:
            current_filtered_df = df[df[column_name] == filter_value]
        elif filter_type == FilterType.STARTSWITH.value:
            current_filtered_df = df[df[column_name].str.startswith(filter_value)]
        filtered_df = pd.concat([filtered_df, current_filtered_df])
    return filtered_df