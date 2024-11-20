#!/usr/bin/python
import os

import pandas as pd
from ..exceptions.expcetion import FileProcessFailException, ConfigMissingException, ResourceNotFoundException
from ..utils.s3_file_parser import S3FileParser
from ..utils.logger import CustomLogger
from ..enums.LogLevel import LogLevel
from ..enums.FilterType import FilterType
from ..enums.ParsedDataResponseType import ParsedDataResponseType
from ..utils import common_utils, file_parser_constants


class FileParser:

    def __init__(self, config):
        self._config = config
        self._logger = CustomLogger()
        self.s3_file_parser = S3FileParser(
            self._logger, self._config)
        self._file_source = None
        self._file_name = ''
        self._file_config = self._config.get("file_config", None)
        try:
            from edgeCases import user_edge_cases
            self.edge_cases = user_edge_cases
        except ImportError:
            self.edge_cases = None
            self._logger.print_log(LogLevel.WARNING.value, message = "FileParser :: Warning: No user-defined edge cases found. Edge case functions won't be available.")

    def get_sheet_names(self, config):
        all_sheet_names = []
        if config is None or file_parser_constants.mark_entry_type_based_on_sheets not in config or file_parser_constants.sheet_type not in config[file_parser_constants.mark_entry_type_based_on_sheets]:
            return all_sheet_names
        all_sheet_names = [sheet_name for sheet_list in config[file_parser_constants.mark_entry_type_based_on_sheets][file_parser_constants.sheet_type].values() for sheet_name in sheet_list]
        return all_sheet_names
    
    def zip_file_reader(self, input_file_path, file_dtype, parameters, skip_footer=0, disable_skip_rows_sheets=[]):
        compression_type = self.file_config.get(file_parser_constants.compression_type, None)
        zfile = self.s3_file_parser.readZipFromS3(input_file_path, compression_type)

        sheet_names = self.get_sheet_names(parameters)
        if len(sheet_names)>0:
            df = self.create_dataframe_with_sheets(zfile, input_file_path, file_dtype, **parameters, skip_footer=skip_footer, disable_skip_rows_sheets=disable_skip_rows_sheets, sheet_names = sheet_names)
        else: 
            df = self.create_dataframe(zfile, input_file_path, file_dtype, **parameters, skip_footer=skip_footer)
        return df
    
    def password_duality_checker(self, input_path_file, password_protected):
        if input_path_file.__contains__("no_password"):
              password_protected=False

        return password_protected

    def fetch_data_from_s3_using_input_path(self, input_file_path=None, file_dtype=None):
        try:
            read_from_s3_func = self.file_config["read_from_s3_func"]
            parameters = self.file_config["parameters_for_read_s3"] if self.file_config["parameters_for_read_s3"] is not None else {}
            skip_footer = 0
            if "skipfooter" in self.file_config and self.file_config.get("skipfooter") > 0:
                skip_footer = self.file_config["skipfooter"]
            if read_from_s3_func == "readFromS3":
                df = self.s3_file_parser.readFromS3(
                    input_file_path, file_dtype, **parameters, skip_footer=skip_footer)
            elif read_from_s3_func == "read_complete_excel_file":
                df = self.s3_file_parser.read_complete_excel_file(
                    input_file_path, file_dtype, skip_footer=skip_footer)
            elif read_from_s3_func == "readZipFromS3":
                disable_skip_rows_sheets = []
                if "disable_skip_rows" in self.file_config and len(self.file_config.get("disable_skip_rows")) > 0:
                    disable_skip_rows_sheets = self.file_config["disable_skip_rows"]
                df = self.zip_file_reader(input_file_path, file_dtype, parameters, skip_footer=skip_footer, disable_skip_rows_sheets=disable_skip_rows_sheets)
        except Exception as e:
            raise Exception(
                "Exception Occurred while Reading from S3 :: "+str(e))
        return df
    
    def ignore_file_while_reading_from_zip(self, file_name, file_type, ignore_file_based_on_extension, ignore_file_based_on_name_list, ignore_file_based_on_name):
        if len(file_type) == 0:
            return True
        if file_type in ignore_file_based_on_extension or (ignore_file_based_on_name is not None and file_name.__contains__(ignore_file_based_on_name)):
            return True
        if file_name in ignore_file_based_on_name_list:
            return True
        return False

    def get_zip_password(self, password_secret_key):
        if password_secret_key == "dynamic_password":
            password = self.get_dynamic_password()
        else:
            password = os.environ[password_secret_key]
        return password

    def create_dataframe(self, zfile, input_file_path, file_dtype=None, password_protected=False, password_secret_key=None, ignore_file_based_on_extension=[], ignore_file_based_on_name_list = [], ignore_file_based_on_name=None, sep=",", header=None, has_header=True, skiprows=0, skip_header=False,engine="c",skip_footer=0):
        df = pd.DataFrame()
        self._logger.print_log(LogLevel.WARNING.value, self._file_name,
                                  "FileParser :: create_dataframe :: Input path = " + input_file_path)
        password_protected = self.password_duality_checker(input_file_path, password_protected)
        
        for fileName in zfile.namelist():
            original_file_name = fileName
            fileName = fileName.split("/")[-1]
            
            file_type = self.s3_file_parser.detect_type(fileName)
            if self.ignore_file_while_reading_from_zip(fileName, file_type, ignore_file_based_on_extension, ignore_file_based_on_name_list, ignore_file_based_on_name):
                continue
            if password_protected:
                password = self.get_zip_password(password_secret_key)
                file_df = self.s3_file_parser.creating_df_based_on_file_types(zfile.open(original_file_name, pwd=bytes(password, 'utf-8')), input_file_path, file_type, file_dtype=file_dtype, header_info={'header': header, 'has_header': has_header, 'skip_header': skip_header}, sep=sep, skiprows=skiprows, engine=engine, skip_footer=skip_footer)
                df = pd.concat([file_df, df], axis=0)
            else:
                file_df = self.s3_file_parser.creating_df_based_on_file_types(zfile.open(original_file_name), input_file_path, file_type, file_dtype=file_dtype, sep=sep, header_info={'header': header, 'has_header': has_header, 'skip_header': skip_header}, skiprows=skiprows, engine=engine, skip_footer=skip_footer)
                df = pd.concat([file_df, df], axis=0)
        return df

    def get_dataframe_for_multiple_sheets(self,sheet_names, zfile, file_name, password, input_file_path, file_type, file_dtype, sep, header, has_header, skiprows, skip_footer=0, disable_skip_rows_sheets=[]):
        dfs={}
        for sheet_name in sheet_names:
            skip_rows = skiprows
            if sheet_name in disable_skip_rows_sheets:
                skip_rows = 0
            dfs[sheet_name] = self.s3_file_parser.creating_df_based_on_file_types(zfile.open(file_name, pwd=bytes(password, 'utf-8') if password else None), input_file_path, file_type, file_dtype=file_dtype, sep=sep, header_info={'header': header, 'has_header': has_header}, skiprows=skip_rows, sheet_name=sheet_name, skip_footer=skip_footer)
            dropna_column = self.file_config.get("dropna_column", None)
        if dropna_column is not None and dropna_column in dfs[sheet_name].columns:
            dfs[sheet_name] = dfs[sheet_name].dropna(subset=[dropna_column])
        return dfs
    
    def create_dataframe_with_sheets(self, zfile, input_file_path, file_dtype=None, password_protected=False, password_secret_key = None, ignore_file_based_on_extension=[], mark_entry_type_based_on_sheets={}, ignore_file_based_on_name="", sep=",", header=None, has_header=True, skiprows=0,skip_footer=0, disable_skip_rows_sheets=[], sheet_names = []):
        dfs = {}
        try:
            for file_name in zfile.namelist():
                file_type = self.s3_file_parser.detect_type(file_name)
                password = None
                if password_protected:
                    password = os.environ[password_secret_key]
                dfs = self.get_dataframe_for_multiple_sheets(sheet_names, zfile, file_name, password, input_file_path, file_type, file_dtype, sep, header, has_header, skiprows,skip_footer=skip_footer, disable_skip_rows_sheets=disable_skip_rows_sheets)

                dfs_by_sheet_type = {}
                for df_type, sheet_names in mark_entry_type_based_on_sheets[file_parser_constants.sheet_type].items():
                    df = pd.DataFrame({})
                    for sheet_name in sheet_names:
                        df = pd.concat([df, dfs[sheet_name]])
                    # Add the specified column with the type (key) as the value
                    df[mark_entry_type_based_on_sheets[file_parser_constants.column_name]] = df_type
                    dfs_by_sheet_type[df_type] = df

                # Concatenate all dataframes into a single dataframe
                final_df = pd.concat(dfs_by_sheet_type.values())
        except Exception as e:
            self._logger.print_log(LogLevel.ERROR.value, self._file_name, "createDataFrame :: Failed to load dataframe :: Error: " + str(e))
            raise FileProcessFailException("createDataFrame::Failed to load dataframe "+str(e))
        return final_df

    def sanitize_file(self, df):
        try:
            self._logger.print_log(LogLevel.WARNING.value, self._file_name,
                                  self._file_source+" :: file size = " + str(df.shape[0])+" :: columns :: "+str(df.columns))
            if df.shape[0] == 0:
                return df
            
            df = self.apply_edge_cases(df)
            
            df.rename(
                columns=self.file_config["columns_mapping"], inplace = True)

            if "filter_based_on_status" in self.file_config and self.file_config["filter_based_on_status"] is not None:
                filter_type = self.file_config["filter_based_on_status"]["filter_type"] if "filter_type" in self.file_config["filter_based_on_status"] else FilterType.EQUALS.value
                filter_column = self.file_config["filter_based_on_status"].get("filter_column", None)
                df = common_utils.filter_entries_by_transaction_types_list(df, filter_column, self.file_config["filter_based_on_status"]["filter_values"], filter_type)
            return df
        except Exception as e:
            raise Exception(
                "Exception Occurred while sanitizing MIS DF :: "+str(e))
    
    def apply_edge_cases(self, df):
        try:
            conditions = self.file_config["edge_case"]
            if conditions is None or len(conditions) < 1:
              return df
            if self.edge_cases is None:
                raise ImportError("Edge case module not found. Please ensure `user_edge_cases` is available in Config.")
            for condition_name, params in conditions.items():
                edge_case_func = getattr(self.edge_cases, condition_name, None)
                
                # If the function is missing, raise an error with details
                if not edge_case_func:
                    raise AttributeError(f"Edge case '{condition_name}' is not defined in `user_edge_cases.py`. Please define it or update the configuration.")
                
                # Call the user-defined function with parameters from config
                if params is None:
                    df = edge_case_func(df)
                else:
                    df = edge_case_func(df, params)
        
            return df
        except Exception as e:
            raise FileProcessFailException(
                  "Exception Occurred while handling edge cases :: "+str(e))

    def parse_file(self, input_file_path=None, file_source = None, response_type = None):
        """
        Fetch file data for given input_path and convert the data in consumable format for generating consolidated report
        Args:
            file_path (str): Path to the file to be parsed.
            file_source: file source name in configuration
        Returns: parsed data as response_type
        """
        self._file_name = os.path.basename(input_file_path)
        self._file_source = file_source
        if self._file_source is None:
            raise ResourceNotFoundException("FileSource")
        
        if self._file_config is None:
            raise ConfigMissingException("File Config is missing")
        
        if self._file_source not in self._file_config:
            raise ConfigMissingException(f"File Config is missing for FileSource = {self._file_source}")

        self.file_config = self._file_config[self._file_source]
        self._logger.print_log(LogLevel.WARNING.value, self._file_name,
                                f"FileParser :: parse_file :: Input path = {input_file_path}")
        file_dtype = self.file_config["file_dtype"]
        df = self.fetch_data_from_s3_using_input_path(input_file_path, file_dtype)

        df = self.sanitize_file(df)

        if response_type == ParsedDataResponseType.JSON.value:
            return df.to_json(orient="records")
        elif response_type == ParsedDataResponseType.FILE.value:
            file_path = f"parsed_{self._file_name}"
            df.to_csv(file_path, index=False)
            try:
                return file_path
            finally:
                os.remove(file_path)  # Clean up the file immediately
        else:
            return df
    
    def get_dynamic_password(self):
            password = ""
            try:
                password_type = self.file_config.get("password_type", None)
                if password_type is None:
                    raise ValueError("The Value of the password type can't be none")
                elif password_type is "password_changes_wrt_time":
                    password = common_utils.get_dynamic_password_based_on_time()
                return password
            except Exception as e:
                self._logger.print_log(LogLevel.EXCEPTION.value, self._file_name,
                                      "Exception Occurred getting dynamic password:: " + str(e))