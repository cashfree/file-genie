## FileGenie SDK
FileGenie SDK is a Python library designed to simplify parsing files from AWS S3 in various formats (e.g., TEXT, CSV, EXCEL, ZIP, XML, PDF) and transforming the data using user-defined functions into desired output formats. By providing file parsing configurations and custom transformation logic, this library effortlessly processes and provide the output as needed.

### Features
- **Multi-format Support:** Effortlessly parse files in formats such as TEXT, CSV, EXCEL, ZIP, XML, and PDF directly from AWS S3.
- **Flexible Response Types:** Generate responses tailored to user needs, including DATAFRAME, JSON, or FILE outputs.
- **Password-Protected Files:** Seamlessly parse files secured with passwords.
- **Custom Edge Case Handling:** Apply user-defined custom functions to address specific data massaging and transformation requirements, such as sanitizing data, converting values, reformatting date fields etc.
- **AWS S3 Integration:** Fetch files directly from AWS S3 buckets using IAM roles for secure access.
- **Streamlined Configuration:** Set up easily with minimal configuration, eliminating the need of writing parser for specific file type.

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
**Define Custom Edge Cases:**
Let's say you need to sanitize columns (e.g., standardise column values to a common format before applying custom logic) during file parsing, you can define custom functions for the SDK to use.

To implement this:

- Create an edgeCases folder in your project.
- Add a file named user_edge_cases.py.
- Define your custom functions in this file.
- Reference these functions in the edge_case section of the file_config.
- The SDK will automatically import and apply these functions during file parsing or transformation.

```
from edgeCases import user_edge_cases
self.edge_cases = user_edge_cases
```

**Define the configuration required for file parsing logic and S3 bucket names**
```
    s3_config: {
        upload_bucket: s3_bucket_name
        download_bucket: s3_bucket_name
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
**read_from_s3_func:** This filed in FileGenie configuration specifies the function to be used for parsing a specific file type from AWS S3. Depending on the file format, you can choose from the following available functions:

- **readFromS3** - parse the TXT, EXCEL, CSV, XML, PDF files
- **readZipFromS3** - parse the zip files
- **read_complete_excel_file** - Use this function when working with EXCEL files containing multiple sheets.

**parameters_for_read_s3:** This field in FileGenie configuration specifies the additional parameters required for reading the file such as password_protected, password, sep etc. you can choose from the following available params:
- password_protected: If file is password protected or not
- passowrd_secret_key: Secret key name for password.
- skiprows: Rows to skip at the start.
- sep: Delimiter for CSV parsing.
- header: Row number(s) to use as column names.
- has_header: Specify if the file has a header.
- skip_header: Skip the header row during processing.
- sheet_name: Target sheet in an Excel file.
- parser_func: Custom parser function.
- chunksize: Number of rows to read per chunk.
- skip_footer: Rows to skip at the end.

**Import and initialise the file genie**
```
from file_genie import FileGenie

file_genie = FileGenie(config={s3_config: s3_config, file_config: file_config})
parsed_data = file_genie.parse("s3://your-bucket-name/path/to/your/file.csv", file_source, ParsedDataResponseType.DATAFRAME.value)
//By default SDK will provide response as DATAFRAME
```

