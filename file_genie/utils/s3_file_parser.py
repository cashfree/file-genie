#!/usr/bin/python
import io
import os
from datetime import datetime
from io import StringIO
from urllib.parse import urlparse
from zipfile import ZipFile
from io import BytesIO
import pyzipper

import boto3
import botocore.config
import pandas as pd
from tabula import read_pdf
import csv
from . import file_parser_constants
from ..exceptions.expcetion import S3Exception, ConfigMissingException
import mt940_utils
from ..enums.LogLevel import LogLevel
from lxml import etree

class S3FileParser:
    def __init__(self, logger, config):
        self._logger = logger
        self._config = config
        self._upload_bucket = self.get_s3_config('upload_bucket')

    def detect_type(self, input_file_path):
        """
        This function will detect the file type.
        Depending on the type, an appropriate library is called to parse the file.
        Ex: csv, txt etc

        :param input_file_path:
        :return: File type (csv, txt, etc)
        """
        self._logger.print_log(LogLevel.INFO.value, "detect_type::Detect File type")
        file_type = os.path.splitext(input_file_path)[1][1:]
        self._logger.print_log(LogLevel.INFO.value, "detect_type::fileType - "+str(file_type))
        return file_type.lower()

    def getS3_object(self, inputFilePath):
        obj = None
        try:
            s3 = boto3.client('s3')
            relativePath = urlparse(inputFilePath).path
            self._logger.print_log(LogLevel.INFO.value, "getS3_object::relativePath = " + str(relativePath[1:]))
            bucket = self.get_s3_config('download_bucket')
            obj = s3.get_object(Bucket=bucket, Key=relativePath[1:])
        except Exception as e:
            self._logger.print_log(LogLevel.EXCEPTION.value,
                                  "exception in reading "+inputFilePath+" in s3 client :"+str(e), exc_info=True)

        return obj

    def convert_pdf_to_df(self, obj_stream):
        dfs = read_pdf(obj_stream, stream=True, pages="all")
        return dfs

    def create_df_from_csv(self, file_name, file_dtype=None, chunksize=None, sep=",", header=None, has_header=True, skiprows=0, skip_header = False, names = None):
        if skip_header is True:
            return pd.read_csv(file_name, dtype=file_dtype, names = names, skiprows=skiprows, index_col=False)
        if has_header is True:
            df = pd.read_csv(file_name, skiprows=skiprows,
                        on_bad_lines='skip', dtype=file_dtype, chunksize=chunksize, sep=sep, index_col=False)
        else:
            df = pd.read_csv(file_name, skiprows=skiprows,
                        on_bad_lines='skip', dtype=file_dtype, chunksize=chunksize, sep=sep, header=header, index_col=False)
        return df

    def create_df_from_excel_file(self, file_name, file_dtype, header, sheet_name, has_header, skiprows):
        if sheet_name is None:
            if has_header is True:
                df = pd.read_excel(io.BytesIO(
                    file_name.read()), dtype=file_dtype, skiprows=skiprows)
            else:
                df = pd.read_excel(io.BytesIO(file_name.read()), dtype=file_dtype, header=header,
                                        skiprows=skiprows)
        else:
            df = pd.read_excel(io.BytesIO(file_name.read()), sheet_name=sheet_name, dtype=file_dtype,
                                skiprows=skiprows)
        return df

    def creating_df_based_on_file_types(self, file_name, input_file_path, file_type, file_dtype=None, chunksize=None, sep=",", parser_func=None, sheet_name=None, skiprows=0, names = None, engine="c", header_info={'header': None, 'has_header': True, 'skip_header': False}, skip_footer=0):
        if file_type in file_parser_constants.csv_file_type:
            # The errors are becasue the payouts and refunds are also in the same file but in a different format
            df = self.create_df_from_csv(file_name, file_dtype=file_dtype, chunksize=chunksize, sep=sep, header=None, has_header=header_info['has_header'], skiprows=skiprows, skip_header = header_info['skip_header'], names = header_info['header'])
        elif file_type in file_parser_constants.excel_file_type:
            df = self.create_df_from_excel_file(file_name, file_dtype, header_info['header'], sheet_name, header_info['has_header'], skiprows)
        elif file_type in file_parser_constants.txt_swt_sta_file_type:
            if header_info['has_header'] is True and isinstance(header_info['header'], list):
                df = pd.read_csv(file_name, skiprows=skiprows, sep=sep, skip_blank_lines=True, dtype=file_dtype,
                                skipinitialspace=True, on_bad_lines='skip', names=header_info['header'],
                                usecols=[i for i in range(len(header_info['header']))],chunksize=chunksize, engine=engine)
            else:
                if parser_func:
                    return parser_func(file_name, input_file_path)
                elif header_info['has_header'] is False and header_info['header'] is None:
                    df = pd.read_csv(file_name, skiprows=skiprows, sep=sep, skipinitialspace=True, header=None,
                                    on_bad_lines='skip', dtype=file_dtype, chunksize=chunksize)
                else:
                    df = pd.read_csv(file_name, skiprows=skiprows, sep=sep, skipinitialspace=True,
                                        on_bad_lines='skip', dtype=file_dtype, chunksize=chunksize)
        elif file_type in file_parser_constants.pdf_file_type:
            return self.convert_pdf_to_df(io.BytesIO(file_name.read()))
        elif file_type in file_parser_constants.xml_file_type:
            tree = etree.parse(file_name)
            root = tree.getroot()  
            txn_blocks = root.findall('.//Txn')
            txn_data = []

            for txn in txn_blocks:
                txn_record = {child.tag: child.text for child in txn if child.tag != 'Fee'}

                fees = txn.findall('.//Fee')
                fee_records = {}
                for i, fee in enumerate(fees):
                    for child in fee:
                        fee_records[f"{child.tag}_{i+1}"] = child.text
                txn_record = {**txn_record, **fee_records}
                txn_data.append(txn_record)
            return pd.DataFrame(txn_data)
        else:
            self._logger.print_log(LogLevel.EXCEPTION.value, "readFromS3::File format not handled")
            raise Exception("Format not handled")
        if skip_footer > 0:
            df = df.iloc[:-skip_footer]
        return df

    def readFromS3(self, input_file_path, file_dtype=None, skiprows=0, sep=",", header=None, sheet_name=None, has_header=True, parser_func=None, chunksize=None, skip_header = False, names = None, skip_footer=0):
        '''
        This function will fetch the file from S3, create a data frame and return the same to the caller.
        In case of pdf, it will also confert the pdf
        @param inputFilePath: Path to s3
        @param file_dtype: any converions that needs to be applied at the column level
        @param skiprows: Number f rows to skip from the starting of the dataframe
        @param sep: what seperator to use to create the DF.
        @param header: list of all headers
        @param sheet_name: In case of xls/xlsx a specific sheet name.
        @param has_header: whether the file already has headers
        @return: a single df for all except for PDF. For PDF it will return a list of dfs
        '''
        self._logger.print_log(LogLevel.INFO.value, "readFromS3::Start")
        file_type = None
        obj = self.getS3_object(input_file_path)
        try:
            file_type = self.detect_type(input_file_path)
            df = self.creating_df_based_on_file_types(obj['Body'], input_file_path, file_type, file_dtype, chunksize, sep,
                                            parser_func, sheet_name, skiprows, names, header_info={'header': header, 'has_header': has_header, 'skip_header': skip_header}, skip_footer=skip_footer)
        except Exception as e:
            self._logger.print_log(LogLevel.EXCEPTION.value, "readFromS3::Failed to load dataframe " + str(e))
            raise Exception(e)
        return df

    def readZipFromS3(self, inputFilePath, compression_type=None):
        '''
        This function will fetch the file from S3, create a data frame and return the same to the caller.
        In case of pdf, it will also confert the pdf
        @param inputFilePath: Path to s3
        @return: list of zip files
        '''

        self._logger.print_log(LogLevel.INFO.value, "readZipFromS3::Start")
        obj = self.getS3_object(inputFilePath)

        try:
            if compression_type == "aes":
              zfile = pyzipper.AESZipFile(BytesIO(obj['Body'].read()))
            else:
              zfile = ZipFile(BytesIO(obj['Body'].read()))
        except Exception as e:
            self._logger.print_log(LogLevel.EXCEPTION.value, "readZipFromS3::Failed to unzip file " + str(e))
            raise Exception(e)
        return zfile

    def read_split_mt940_from_s3(self, input_file_path, parser_func):
        self._logger.print_log(LogLevel.INFO.value, "read_split_mt940_from_s3 :: Start")
        obj = self.getS3_object(input_file_path)
        try:
            file_name = mt940_utils.join_mt940_statements(obj['Body'])
            file_type = self.detect_type(file_name)
            df = self.creating_df_based_on_file_types(file_name, input_file_path, file_type, parser_func=parser_func)
            self.delete_file(file_name)
            return df
        except Exception as e:
            self._logger.print_log(
                LogLevel.EXCEPTION.value, "read_split_mt940_from_s3 :: Failed to concatenate the file :: "
                                                        "" + str(e))
            raise S3Exception(e)

    def read_file_from_s3(self, input_file_directory, input_file_path):
        self._logger.print_log(LogLevel.INFO.value, "read_from_s3::Start:: report input_file_directory "
                                                                 "%s, input_file_path = %s " % (str(input_file_directory), str(input_file_path)))
        try:
            s3 = boto3.client('s3')
            obj = s3.get_object(Bucket=input_file_directory,
                                Key=input_file_path)
            return obj
        except Exception as e:
            self._logger.print_log(
                LogLevel.EXCEPTION.value, "read_from_s3:: exception :: " + str(e))
            raise S3Exception(e)

    def read_complete_excel_file(self, inputFilePath, file_dtype, return_df_list=False, skip_footer=0):

        self._logger.print_log(LogLevel.INFO.value, "read_complete_excel_file::Start")
        try:
            s3 = boto3.client('s3')
            relativePath = urlparse(inputFilePath).path
            self._logger.print_log(LogLevel.INFO.value, "read_complete_excel_file::relativePath = " + str(relativePath[1:]))
            bucket = self.get_s3_config('download_bucket')
            obj = s3.get_object(Bucket=bucket, Key=relativePath[1:])
            xl = pd.ExcelFile(io.BytesIO(obj['Body'].read()))
            df_list = []
            if(return_df_list==True):
                for name in xl.sheet_names:
                    df = pd.read_excel(xl, sheet_name=name, dtype=file_dtype,header=None)
                    if skip_footer > 0:
                        df = df.iloc[:-skip_footer]
                    df_list.append(df)
                return df_list
            for name in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=name, dtype=file_dtype)
                if skip_footer > 0:
                    df = df.iloc[:-skip_footer]
                df[file_parser_constants.sheet_name] = name
                df_list.append(df)
            df = pd.concat(df_list)
            return df
        except Exception as e:
            self._logger.print_log(LogLevel.EXCEPTION.value, "read_complete_excel_file::Failed to load dataframe" + str(e))
            raise Exception(e)

    def upload_to_s3(self, df, file_name, product_folder=None, get_signed_url=None, link_expiry=None, return_path=False, base_location=None, sep=",", use_default_file_name=True):
        try:
            self._logger.print_log(LogLevel.INFO.value, "upload_to_s3::File name = " + file_name)

            csv_buffer = self.df_to_csv(df, sep)
            s3_resource = boto3.resource("s3")
            # Write buffer to S3 object
            now = datetime.now()

            prefix_path = self.get_s3_config('backup_path')
            if base_location:
                prefix_path = self.get_s3_config(base_location)

            product_path = ""
            if product_folder is not None:
                product_path = product_folder + "/"
            file_path_prefix = prefix_path + str(now.year) + "_" + str(now.month) + "_" + str(now.day) + "/" + product_path
            if use_default_file_name:
                file_path = file_path_prefix + str(now.hour) + "_" + str(
                    now.minute) + "_" + str(now.second) + "_" + file_name + ".csv"
            else:
                file_path = file_path_prefix + file_name
            s3_resource.Object(self._upload_bucket, file_path).put(
                Body=csv_buffer.getvalue())
            self._logger.print_log(LogLevel.INFO.value, "upload_to_s3::Upload successful")
            if not get_signed_url:
                return

            self._logger.print_log(LogLevel.INFO.value, "upload_to_s3::Link Requested")
            s3_client = boto3.client("s3",
                                     config=botocore.config.Config(
                                         signature_version='s3v4',
                                         region_name='ap-south-1')
                                     )
            url = self.create_presigned_url(
                s3_client, self._upload_bucket, file_path, link_expiry)
            if return_path:
                return url, file_path
            return url
        except Exception as e:
            self._logger.print_log(LogLevel.EXCEPTION.value, "upload_to_s3::Failed to write to DB " +str(e))
            raise Exception(e)

    def upload_file_to_s3(self, input_file_directory, input_file_path, data_frame):
        self._logger.print_log(LogLevel.INFO.value, "upload_file_to_s3:: bucket :: " +
                          input_file_directory + "File path :: " + input_file_path)
        try:
            s3 = boto3.resource('s3')

            csv_buffer = StringIO()
            data_frame.to_csv(csv_buffer, sep=",",
                              quoting=csv.QUOTE_NONNUMERIC, index=False)
            s3.Object(input_file_directory, input_file_path).put(
                Body=csv_buffer.getvalue())
            self._logger.print_log(
                LogLevel.INFO.value, "upload_to_s3 :: Upload successful")
        except Exception as e:
            self._logger.print_log(
                LogLevel.EXCEPTION.value, "upload_to_s3:: exception" + str(e))
            raise S3Exception(e)

    def create_presigned_url(self, s3_client, bucket_name, object_name, expiration=86400):
        self._logger.print_log(LogLevel.INFO.value, "create_presigned_url :: requested-file")
        params = {
            "Bucket": bucket_name,
            "Key": object_name
        }
        signed_url = s3_client.generate_presigned_url(
            ClientMethod='get_object', Params=params, ExpiresIn=expiration)
        return signed_url

    #helps to handle failure if configs are not received from yaml file
    def get_s3_config(self, bucket_name, inputFilePath=None):

      if self._config is not None and 's3_config' in self._config:
        if inputFilePath is not None:
          self._logger.print_log(LogLevel.INFO.value, "reading from S3 from YAML :: input_file_directory %s" % (str(inputFilePath)))
        return self._config.get('s3_config').get(bucket_name)
      else:
        raise ConfigMissingException("Bucket Not Found in Config")

    def df_to_csv(self, df, delim=","):
        local_buffer = StringIO()
        if delim == "~~":
            local_buffer = df.to_csv(index=False)
            local_buffer = StringIO(local_buffer)
            buffer_data = local_buffer.read()
            buffer_data = buffer_data.replace(",", delim)
            local_buffer.seek(0)
            local_buffer.write(buffer_data)
            local_buffer.seek(0)
        elif delim != ",":
            df.to_csv(local_buffer, sep=delim, index=False)
        else:
            df.to_csv(local_buffer, sep=delim,
                      quoting=csv.QUOTE_NONNUMERIC, index=False)
        return local_buffer
    
    def delete_file(self, file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            self._logger.print_log(LogLevel.EXCEPTION.value, f"delete_file :: error occurred while trying to delete the "
                                                        f"file: {e}")