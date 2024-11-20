from unittest import mock
from unittest.mock import mock_open
from file_genie.utils.s3_file_parser import S3FileParser
from file_genie.utils.logger import CustomLogger
import pandas as pd
import pytest, os

mock_df = pd.DataFrame({
    'Transaction Type': ['SALE', 'SALE', 'REFUND', 'CHARGEBACK', 'RP', 'CB_REV'],
    'Payment Mode': ['CRD', 'CRD', 'CRD', 'CRD', 'CRD', 'CRD'],
    'Merchant Name': ['x', 'x', 'y', 'y', 'z', 'z'],
})


class TestCommonService:
    _config = {
        "upload_bucket":"test-bucket",
        "download_bucket":"test-bucket"
    }
    _logger = CustomLogger()
    _s3_file_parser = S3FileParser(_logger, _config)
    _mock_input_path_csv = "test.csv"
    _mock_input_path_xlsx = "test.xlsx"
    _mock_input_path_txt = "test.txt"
    _mock_input_path_pdf = "test.pdf"

    def test_creatingDFBasedOnFileTypes_csv(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.pd.read_csv',
                     return_value=mock_df)
        df = self._s3_file_parser.creating_df_based_on_file_types(self._mock_input_path_csv, self._mock_input_path_csv,
                                                                  "csv")
        assert len(df.columns) == len(mock_df.columns)

    def test_creatingDFBasedOnFileTypes_xlsx(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.pd.read_excel',
                     return_value=mock_df)
        b = bytes(self._mock_input_path_xlsx, 'utf-8')
        with mock.patch("builtins.open", mock_open(read_data=b)) as mock_file:
            df = self._s3_file_parser.creating_df_based_on_file_types(open("path/to/open"), self._mock_input_path_csv,
                                                                      "xlsx")
        assert len(df.columns) == len(mock_df.columns)

    def test_creatingDFBasedOnFileTypes_xlsx_withoutHeader(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.pd.read_excel',
                     return_value=mock_df)
        b = bytes(self._mock_input_path_xlsx, 'utf-8')
        with mock.patch("builtins.open", mock_open(read_data=b)) as mock_file:
            df = self._s3_file_parser.creating_df_based_on_file_types(open("path/to/open"), self._mock_input_path_csv,
                                                                      "xlsx", {'has_header': False})
        assert len(df.columns) == len(mock_df.columns)

    def test_creatingDFBasedOnFileTypes_xlsx_with_sheet_name(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.pd.read_excel',
                     return_value=mock_df)
        b = bytes(self._mock_input_path_xlsx, 'utf-8')
        with mock.patch("builtins.open", mock_open(read_data=b)) as mock_file:
            df = self._s3_file_parser.creating_df_based_on_file_types(open("path/to/open"), self._mock_input_path_csv,
                                                                      "xlsx", {'has_header': False},
                                                                      sheet_name="Sheet1")
        assert len(df.columns) == len(mock_df.columns)

    def test_creatingDFBasedOnFileTypes_txt(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.pd.read_csv',
                     return_value=mock_df)
        header = [{
            'RRN Number': str,
            'PG reference ID': str,
            'Merchant ID': str,
            'Merchant reference number': str,
            'Issuer reference number': str,
            'ARN': str
        }]
        df = self._s3_file_parser.creating_df_based_on_file_types(self._mock_input_path_txt, self._mock_input_path_csv,
                                                                  "txt",
                                                                  header_info={'header': header, 'has_header': True})
        assert len(df.columns) == len(mock_df.columns)

    def test_creatingDFBasedOnFileTypes_txt_without_header(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.pd.read_csv',
                     return_value=mock_df)
        df = self._s3_file_parser.creating_df_based_on_file_types(self._mock_input_path_txt, self._mock_input_path_csv,
                                                                  "txt", {'has_header': False})
        assert len(df.columns) == len(mock_df.columns)

    def test_creatingDFBasedOnFileTypes_pdf(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.convert_pdf_to_df', return_value=mock_df)
        b = bytes(self._mock_input_path_pdf, 'utf-8')
        with mock.patch("builtins.open", mock_open(read_data=b)) as mock_file:
            df = self._s3_file_parser.creating_df_based_on_file_types(open("path/to/open"), self._mock_input_path_pdf,
                                                                      "pdf", header_info={'has_header': False})
        assert len(df.columns) == len(mock_df.columns)

    def test_creatingDFBasedOnFileTypes_unexpected_file_type(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.convert_pdf_to_df', return_value=mock_df)
        b = bytes("abc.img", 'utf-8')
        with mock.patch("builtins.open", mock_open(read_data=b)) as mock_file:
            with pytest.raises(Exception) as e:
                df = self._s3_file_parser.creating_df_based_on_file_types(open("path/to/open"),
                                                                          self._mock_input_path_pdf, "img",
                                                                          header_info={'has_header': False})

    def test_readFromS3_success(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.getS3_object')
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.detect_type', return_value="csv")
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.creating_df_based_on_file_types', return_value=mock_df)
        df = self._s3_file_parser.readFromS3(self._mock_input_path_csv, "csv", "")
        assert len(df.columns) == len(mock_df.columns)

    def test_readFromS3_exception(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.detect_type', return_value="csv")
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.creating_df_based_on_file_types')
        with pytest.raises(Exception) as e:
            df = self._s3_file_parser.readFromS3(self._mock_input_path_csv, "csv", "")

    def test_delete_existing_file(self):
        file_path = "test_file.txt"
        with open(file_path, "w") as test_file:
            test_file.write("Test content")
        self._s3_file_parser.delete_file("non_existing_file.txt")
        self._s3_file_parser.delete_file(file_path)
        assert os.path.exists(file_path) is False

    def test_call_update_txn_mock(self, mocker):
        mock_transactionId = "T_Id123"
        mock_amount = 100
        mock_status = True
        expected_output = None
        actual_output = self._s3_file_parser.call_update_txn_mock(mock_transactionId, mock_amount, mock_status)
        assert expected_output == actual_output

    def test_read_split_mt940_from_s3_success(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.getS3_object')
        mocker.patch('file_genie.utils.s3_file_parser.mt940_utils.join_mt940_statements', return_value="file_name.txt")
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.detect_type', return_value="csv")
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.delete_file')
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.creating_df_based_on_file_types', return_value=mock_df)
        df = self._s3_file_parser.read_split_mt940_from_s3(self._mock_input_path_csv, None)
        assert len(df.columns) == len(mock_df.columns)

    def test_read_split_mt940_from_s3_exception(self, mocker):
        mocker.patch('file_genie.utils.s3_file_parser.mt940_utils.join_mt940_statements', return_value="file_name.txt")
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.detect_type', return_value="csv")
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.creating_df_based_on_file_types')
        mocker.patch('file_genie.utils.s3_file_parser.S3FileParser.delete_file')
        with pytest.raises(Exception) as e:
            df = self._s3_file_parser.read_split_mt940_from_s3(self._mock_input_path_csv, None)
