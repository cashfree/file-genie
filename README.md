## FileGenie SDK
FileGenie SDK is a Python library designed to simplify the parsing of various file formats (eg. TEXT, CSV, EXCEL, ZIP, XML, PDF) with a customizable transforming payloads as required. This SDK offers seamless integration, efficient file handling, and the flexibility to address edge cases with user-defined logic tailored to transforming entries as needed.

### Features
- **Multi-format Support:** Parse TEXT, CSV, EXCEL, ZIP, XML and PDF files effortlessly from AWS S3.
- **Multi-format Response:** Supports multiple type of response as per user's need. For eg.- DATAFRAME, JSON, FILE
- **Password-Proctected Support:** Parse password protected files.
- **Customizable Edge Case Handling:** Define and apply custom functions to handle specific parsing requirements. There can be multiple edge case to handle while transforming the entries such as sanitise_str_column, convert_amount_as_per_currency, convert_date_format etc.
- **S3 Integration:** Supports fetching files directly from AWS S3 buckets based on IAM role.
- **Simple Configuration:** Initialize with straightforward configurations, avoiding the need for additional setup files.

### Installation
Install the SDK using pip:
```
pip install file_genie
```

### Prerequisites
- **Your application should be deployed on AWS EKS to enable the SDK to utilize AWS S3 credentials.**
- **Python:** >= '3.6'
- **Pandas:** '2.0.0'

### Getting Started
- **Define Custom Edge Cases:**
When specific functions are needed during file parsing, the SDK will import edge cases from your project structure as shown below. To implement this, create an edgeCases folder in your project and add a file named user_edge_cases.py. Define your custom functions in this file, and reference them in the edge_case section within the file_config as shown below.
```
from edgeCases import user_edge_cases
self.edge_cases = user_edge_cases
```

- **Define the configuration required for file parsing logic and S3 bucket names**
```
    s3_config: {
        upload_bucket: reconciliation-live
        download_bucket: reconciliation-live
    }
    file_config: {
        "file_source_1": {
            "read_from_s3_func":"read_complete_excel_file",
            "parameters_for_read_s3": None,
            "file_dtype":{
                "Order_Number": str,
                "Added On":str,
                "Added By":str
            },
            "columns_mapping": {
                <!-- "Column Name in file": "Column name required in output" -->
                "Transaction Type": "TransactionType",
                "Cust Name": "CustomerName",
                "Cust ID": "CustomerId",
                "Transaction Amount": "Amount",
                "OrderNumber": "TransactionReference",
                "Reference ID": "CustomerReferenceId",
                "Target Date": "TargetDate",
                "TransactionDate": "TransactionDate",
                "FeeAmount": "ServiceCharge",
                "TaxAmount": "ServiceTax",
                "NetAmount": "NetAmount"
            }
            "edge_case": {
                <!-- edge case function name which you have defined in user_edge_case.py : params required for that function
                there can be different type of params. For eg. - dict, list, str -->
                <!-- In this convert_amount_as_per_currency is the edge case function which you want to apply while transforming the entries and "Amount" is the param to this function where you will apply the currency conversion -->
                "convert_amount_as_per_currency": "Amount"
            }
        },
    }
```

- **Define a ParsedDataResponseType enum**
```
import enum
class ParsedDataResponseType(enum.Enum):
    DATAFRAME="DATAFRAME"
    FILE="FILE"
    JSON="JSON"
```

- **Import and initialise the file genie**
```
from file_genie import FileGenie

file_genie = FileGenie(config={s3_config: s3_config, file_config: file_config})
parsed_data = file_genie.parse("s3://your-bucket-name/path/to/your/file.csv", file_source, ParsedDataResponseType.DATAFRAME.value)
//By default SDK will provide response as DATAFRAME
```

