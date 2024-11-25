
from setuptools import setup, find_packages

setup(
    name="file_genie",
    version="0.0.4",
    description="File Genie is designed to parse various file types and transform them according to provided configuration",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Dinesh Lakhara",
    author_email='dinesh.lakhara@cashfree.com',
    packages=find_packages(include=["file_genie", "file_genie.*"], exclude=["test", "test.*"]),
    include_package_data=True,
    install_requires=[
        "boto3==1.12.42",
        "botocore==1.15.49",
        "pandas>=2.0.0, <=2.2.3",
        "mt-940==4.23.0",
        "xlrd==2.0.1",
        "openpyxl==3.1.2",
        "s3fs==0.4.2",
        "s3transfer==0.3.3",
        "python-dateutil==2.8.2",
        "pytz==2020.1",
        "json-logging==1.2.0",
        "pyzipper==0.3.6",
        "lxml==5.2.2",
        "tabula-py==2.1.1"
    ],
    python_requires=">=3.6",
)