import copy, pytest
from file_genie.service.file_parser import FileParser
import pandas as pd
from unittest import mock
from unittest.mock import MagicMock



mock_df = pd.DataFrame({
    "MisTransactionType": ['SALE', 'SALE', 'REFUND', 'CHARGEBACK', 'RP', 'CB_REV'],
    "MisPaymentMode": ['CRD', 'CRD', 'CRD', 'CRD', 'CRD', 'CRD'],
    "MisMerchantName": ['x', 'x', 'y', 'y', 'z', 'z'],
    "MisMerchantId": [1, 1, 2, 2, 3, 3],
    "MisUrn": ['4567890', '456781', '456712', '456123', '451234', '412345'],
    "MisArn": ['4567890', '456781', '456712', '456123', '451234', '412345'],
    "MisCardScheme": ['VISA', 'VISA', 'VISA', 'VISA', 'VISA', 'VISA'],
    "MisSettlementDate": ['19-05-2022', '19-05-2022', '19-05-2022', '19-05-2022', '19-05-2022', '19-05-2022'],
    "MisSettlementAmount": [123, 23.45, 34, 45, 67, 43],
    "MisServiceCharge": [1, 2.05, 3, 4, 5.60, 2.30],
    "MisCgst": [0, 0, 0, 0, 0, 0],
    "MisSgst": [0, 0, 0, 0, 0, 0],
    "MisIgst": [1, 2.5, 0, 0, 1.09, 0],
    "MisNetSettlementAmount": [123, 23.45, 34, 45, 67, 43],
    "MisAmount": [123, 23.45, 34, 45, 67, 43],
    "MisTxRef": ['961326679', '962316679', '961316679', '961326679', '921316679', '911316679'],
    "MisIssuerReferenceNumber": ['234567', '345678', '456789', '567890', '678901', '789012'],
    "MisPgReferenceId": ['456123', '356123', '256123', '156123', '446123', '454123'],
    "MisCardType": ['DEBIT', 'DEBIT', 'DEBIT', 'CREDIT', 'DEBIT', 'DEBIT'],
    "MisSettlementCurrency": ['INR', 'INR', 'INR', 'INR', 'INR', 'INR'],
    "MisAuthId": [5678, 7689, 9876, 7890, 3467, 8976],
    "MisCardNumber": ['568954xxxx5678', '568954xxxx5688', '568954xxxx5698', '568954xxxx5600', '568954xxxx5671', '568954xxxx5665'],
    "MisGstNumber": ['456789098765', '456789898765', '459889098765', '453489098765', '433789098765', '56789098765'],
    "MisDateTime": ['18-05-2022 01:47:02', '18-05-2022 11:47:02', '18-05-2022 09:47:02',
                            '18-05-2022 18:47:02', '18-05-2022 16:47:02', '17-05-2022 17:47:02'],
    "MisDomesticAmount": [123, 23.45, 34, 45, 67, 43]
})



class TestMISTemplateParser:
    _config = {
        "file_config": {
        "file_source_1": {
            "read_from_s3_func":"read_complete_excel_file",
            "parameters_for_read_s3": None,
            "file_dtype":{
                "Order_Number": str,
                "PG_Ref":str,
                "AG_Ref":str
            },
            "map_based_on_txn_type":False,
            "columns_mapping":{
                "Transaction_Type": "MisTransactionType",
                "Merchant_Name": "MisMerchantName",
                "Merchant_ID": "MisMerchantId",
                "Amount": "MisAmount",
                "Order_Number": "MisTxRef",
                "PG_Ref": "MisPgReferenceId",
                "Settlement_Date": "MisSettlementDate",
                "Transaction_Date": "MisDateTime",
                "Fee": "MisServiceCharge",
                "ME_IGST": "MisServiceTax",
                "Net_Amount":"MisNetSettlementAmount"
            },
            "edge_case": {
                "add_reversal_tx_ref_column": "reversal_txRef"
            }
            },
        },
        "s3_config": {
        "upload_bucket":"test-bucket",
        "download_bucket":"test-bucket"
        }
    }
    _mis_template_parser = FileParser(_config)
    mock_input_file_path = "s3://bucket/key"
    _mock_df = copy.deepcopy(mock_df)

    def test_zip_file_reader_with_sheet_names(self, mocker):
        mock_s3_file_parser = mocker.Mock()
        mock_s3_file_parser.readZipFromS3.return_value = mock.Mock()
        parameters = {
            "sale_sheet_names": ["Sheet1"],
            "refund_sheet_names": [],
            "chargeback_sheet_names": []
        }
        self._mis_template_parser._file_config = {'compression_type': 'zip'}
        self._mis_template_parser.s3_file_parser = mock_s3_file_parser
        mock_create_dataframe_with_sheets = mocker.patch.object(self._mis_template_parser, 'create_dataframe_with_sheets')
        mock_create_dataframe_with_sheets.return_value = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        df = self._mis_template_parser.zip_file_reader("test.zip", "csv", parameters)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        mock_create_dataframe_with_sheets.assert_called_once_with(mock.ANY, "test.zip", "csv", **parameters, skip_footer=0, disable_skip_rows_sheets=[])

    def test_zip_file_reader_without_sheet_names(self, mocker):
        mock_s3_file_parser = mocker.Mock()
        mock_s3_file_parser.readZipFromS3.return_value = mock.Mock()
        parameters = {}
        self._mis_template_parser._file_config = {'compression_type': 'zip'}
        self._mis_template_parser.s3_file_parser = mock_s3_file_parser
        mock_create_dataframe = mocker.patch.object(self._mis_template_parser, 'create_dataframe')
        mock_create_dataframe.return_value = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        df = self._mis_template_parser.zip_file_reader("test.zip", "csv", parameters)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        mock_create_dataframe.assert_called_once_with(mock.ANY, "test.zip", "csv", **parameters, skip_footer=0)

    def test_fetch_data_from_s3_using_input_path_with_readFromS3(self, mocker):
        mock_file_dtype = "csv"
        mock_readFromS3 = mocker.patch.object(self._mis_template_parser.s3_file_parser, "readFromS3")
        mock_readFromS3.return_value = pd.DataFrame([{"col1": 1, "col2": 2}])
        self._mis_template_parser._file_config = {
            "read_from_s3_func": "readFromS3",
            "parameters_for_read_s3": {
                "key": "value"
            }
        }
        mock_df = self._mis_template_parser.fetch_data_from_s3_using_input_path(self.mock_input_file_path, mock_file_dtype)
        mock_readFromS3.assert_called_once()
        assert mock_df.equals(pd.DataFrame([{"col1": 1, "col2": 2}]))

    def test_fetch_data_from_s3_using_input_path_with_read_complete_excel_file(self, mocker):
        mock_file_dtype = "xlsx"
        mock_read_complete_excel_file = mocker.patch.object(self._mis_template_parser.s3_file_parser,"read_complete_excel_file")
        mock_read_complete_excel_file.return_value = pd.DataFrame([{"col1": 1,"col2": 2}])
        self._mis_template_parser._file_config = {
            "read_from_s3_func": "read_complete_excel_file",
            "parameters_for_read_s3": None
        }
        mock_df = self._mis_template_parser.fetch_data_from_s3_using_input_path(self.mock_input_file_path, mock_file_dtype)
        mock_read_complete_excel_file.assert_called_once()
        assert mock_df.equals(pd.DataFrame([{"col1": 1, "col2": 2}]))

    def test_fetch_data_from_s3_using_input_path_zip(self, mocker):
        # Define inputs for the function
        mock_input_path = "s3://bucket/folder/file.zip"
        mock_file_dtype = "csv"
        parameters = {"compression": "zip"}
        mock_skip_footer = 0

        # Define expected output
        expected_output = "test_dataframe"

        # Mock the zip_file_reader method
        mock_zip_file_reader = mocker.patch.object(self._mis_template_parser, "zip_file_reader")
        mock_zip_file_reader.return_value = expected_output

        # Set the read_from_s3_func variable to "readZipFromS3"
        self._mis_template_parser._file_config["read_from_s3_func"] = "readZipFromS3"
        self._mis_template_parser._file_config["parameters_for_read_s3"] = parameters

        # Call the function
        actual_output = self._mis_template_parser.fetch_data_from_s3_using_input_path(
            mock_input_path, mock_file_dtype)

        # Check that the zip_file_reader method was called with the correct inputs
        mock_zip_file_reader.assert_called_once_with(
            mock_input_path, mock_file_dtype, parameters, skip_footer=mock_skip_footer, disable_skip_rows_sheets=[])

        # Check that the actual output matches the expected output
        assert actual_output == expected_output

    def test_fetch_data_from_s3_using_input_path_exception(self, mocker):
        mock_error = "mocked error"
        mocker.patch('file_genie.service.file_parser.S3FileParser.readFromS3',
                     side_effect=Exception(mock_error))

        with pytest.raises(Exception) as e:
            self._mis_template_parser.fetch_data_from_s3_using_input_path(self.mock_input_file_path)
            e.value==mock_error
    
    def test_create_dataframe(self, mocker):
        # create mock objects
        mock_s3_file_parser = mocker.MagicMock()
        zfile_mock = MagicMock()
        file_mock = MagicMock()

        mocker.patch('file_genie.service.file_parser.FileParser.password_duality_checker',
                     return_value=False)
        # setup mock return values
        zfile_mock.namelist.return_value = ["file1.csv", "file2.xlsx"]
        mock_s3_file_parser.detect_type.side_effect = ["csv", "xlsx"]
        mock_s3_file_parser.creating_df_based_on_file_types.side_effect = [
            pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}),
            pd.DataFrame({'C': [7, 8, 9], 'D': [10, 11, 12]})
        ]

        # Mock attributes of the instance
        self._mis_template_parser.s3_file_parser = mock_s3_file_parser
        mocker.patch('file_genie.service.file_parser.FileParser.ignore_file_while_reading_from_zip',
                     side_effect=[True, False])
        # call the method to test
        df = self._mis_template_parser.create_dataframe(zfile_mock, "test.zip", ignore_file_based_on_extension=["xlsx"])

        # assert the expected values
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        common_service_mock.detect_type.assert_has_calls([mocker.call("file1.csv"), mocker.call("file2.xlsx")])
        common_service_mock.creating_df_based_on_file_types.assert_called_once()

    def test_create_dataframe_1(self, mocker):
        common_service_mock = mocker.MagicMock()
        zfile_mock = MagicMock()

        mocker.patch('file_genie.service.file_parser.FileParser.password_duality_checker',
                     return_value=False)
        # setup mock return values
        zfile_mock.namelist.return_value = ["folder1", "file1.csv", "file2.xlsx","file3.csv"]
        common_service_mock.detect_type.side_effect = ["","csv", "xlsx", "csv"]
        common_service_mock.creating_df_based_on_file_types.side_effect = [
            pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}),
            pd.DataFrame({'C': [7, 8, 9], 'D': [10, 11, 12]})
        ]
        # Mock attributes of the instance
        self._mis_template_parser._common_service = common_service_mock
        mocker.patch('file_genie.service.file_parser.FileParser.ignore_file_while_reading_from_zip',
                     side_effect=[True,True,True,False])
        # call the method to test
        df = self._mis_template_parser.create_dataframe(zfile_mock, "test.zip", ignore_file_based_on_name_list=["file1.csv", "file2.xlsx"])

        # assert the expected values
        assert len(df) == 3
        common_service_mock.detect_type.assert_has_calls([mocker.call("folder1"), mocker.call("file1.csv"), mocker.call("file2.xlsx"), mocker.call("file3.csv")])
        common_service_mock.creating_df_based_on_file_types.assert_called_once()
    
    def test_create_dataframe_password_protected(self, mocker):
        common_service_mock = mocker.MagicMock()
        zfile_mock = MagicMock()

        mocker.patch('file_genie.service.file_parser.FileParser.password_duality_checker',
                     return_value=True)
        # setup mock return values
        zfile_mock.namelist.return_value = ["folder1", "file1.csv", "file2.xlsx","file3.csv"]
        common_service_mock.detect_type.side_effect = ["","csv", "xlsx", "csv"]
        common_service_mock.creating_df_based_on_file_types.side_effect = [
            pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}),
            pd.DataFrame({'C': [7, 8, 9], 'D': [10, 11, 12]})
        ]

        # Mock attributes of the instance
        self._mis_template_parser._common_service = common_service_mock
        mocker.patch('file_genie.service.file_parser.FileParser.ignore_file_while_reading_from_zip',
                     side_effect=[True,True,True,False])
        # call the method to test
        df = self._mis_template_parser.create_dataframe(zfile_mock, "test.zip", ignore_file_based_on_name_list=["file1.csv", "file2.xlsx"], password_protected=True, password_secret_key="CYB_HDFC_ZIP_PASSWORD")

        # assert the expected values
        assert len(df) == 3
        common_service_mock.detect_type.assert_has_calls([mocker.call("folder1"), mocker.call("file1.csv"), mocker.call("file2.xlsx"), mocker.call("file3.csv")])
        common_service_mock.creating_df_based_on_file_types.assert_called_once()
    

    def test_create_dataframe_exception(self, mocker):
        # create mock objects
        zfile_mock = MagicMock()

        # setup mock return values
        zfile_mock.namelist.side_effect = Exception('An exception occurred')

        # call the method to test and assert that it raises the expected exception
        with pytest.raises(Exception, match='Exception Occurred while Creating DF from Zip :: An exception occurred'):
            df = self._mis_template_parser.create_dataframe(zfile_mock, "test.zip", ignore_file_based_on_extension=["xlsx"])

    def test_sanitize_mis_file_exception(self, mocker):
        mock_exception = Exception("test exception")
        
        # mock the code that may raise an exception
        with pytest.raises(Exception, match="Exception Occurred while sanitizing MIS DF :: test exception"):
            # raise the mocked exception
            raise Exception("Exception Occurred while sanitizing MIS DF :: "+str(mock_exception))


    def test_get_dynamic_password_with_valid_config(self, mocker):
        # Setup
        self._mis_template_parser._mis_file_config = {"password_type": "password_changes_wrt_time"}
        expected_password = "example_password"

        # Mock the external function being called
        with mock.patch("file_genie.service.file_parser.FileParser.get_dynamic_password_based_on_time", return_value=expected_password):
            # Execute
            password = self._mis_template_parser.get_dynamic_password()

        # Assert
        assert password == expected_password

    def test_get_dynamic_password_exception(self, mocker):
        mock_error = 'mocked_error'
        mocker.patch('file_genie.service.file_parser.FileParser.get_dynamic_password_based_on_time',
                     side_effect=Exception(mock_error))
        with pytest.raises(Exception) as e:
            self._mis_template_parser.get_dynamic_password()
            e.value==mock_error

    def test_get_zip_password(self, mocker):
        mock_password_secret_key = "dynamic_password"
        mock_password = "pest_password"
        mocker.patch('file_genie.service.file_parser.FileParser.get_dynamic_password', return_value=mock_password)
        password = self._mis_template_parser.get_zip_password(mock_password_secret_key)
        assert password == mock_password

    def test_ignore_file_while_reading_from_zip(self):
        res = self._mis_template_parser.ignore_file_while_reading_from_zip("test.csv","csv",[],[],None)
        assert res==False

    def test_ignore_file_while_reading_from_zip_case2(self):
        res = self._mis_template_parser.ignore_file_while_reading_from_zip("test.csv","csv",["csv"],[],None)
        assert res==True

    def test_ignore_file_while_reading_from_zip_case3(self):
        res = self._mis_template_parser.ignore_file_while_reading_from_zip("test.csv","csv",[],["test.csv"],None)
        assert res==True

    def test_ignore_file_while_reading_from_zip_case4(self):
        res = self._mis_template_parser.ignore_file_while_reading_from_zip("test.csv","",[],[],None)
        assert res==True

    def test_ignore_file_while_reading_from_zip_case5(self):
        res = self._mis_template_parser.ignore_file_while_reading_from_zip("test.csv","csv",[],[],"test")
        assert res==True
    
    def test_password_duality_checker(self):
        password_protected = self._mis_template_parser.password_duality_checker("no_password", True)
        assert password_protected == False
    
    def test_process_mis_file(self, mocker):
        self._mis_template_parser._pg = "cybyes"
        self._mis_template_parser._file_config = {
            "threshold": 2000,
            "file_dtype":{'RRN Number': str,
                        'PG reference ID': str,
                        'Merchant ID': str,
                        'Merchant reference number': str,
                        'Issuer reference number': str,
                        'ARN': str},
            "edge_case": None
        }
        mocked_fetch_data_from_s3_using_input_path = mocker.patch(
            'file_genie.service.file_parser.FileParser.fetch_data_from_s3_using_input_path', return_value=self._mock_df)
        mocked_sanitize_mis_file = mocker.patch(
            'file_genie.service.file_parser.FileParser.sanitize_mis_file', return_value=self._mock_df)

        self._mis_template_parser.parse_file("xyz")
        mocked_fetch_data_from_s3_using_input_path.assert_called_once()
        mocked_sanitize_mis_file.assert_called_once()