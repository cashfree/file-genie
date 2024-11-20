# src/__init__.py
from .service.file_parser import FileParser

class FileGenie:
    def __init__(self, config):
        """
        Initialize the SDK with configuration.
        
        Args:
            config (dict): Configuration dictionary (e.g., file_config, s3_config).
        """
        self.config = config
        self.parser = FileParser(config)

    def parse(self, file_path: str, file_source: str = None, response_type: str = None):
        """
        Parse and transform file as per mapping defined in configuration
        Args:
            file_path (str): Path to the file to be parsed.
            file_source: file source name in configuration
        
        Returns:
            Result of the parsing data as ParsedDataResponseType
            Defualt: Dataframe
        """
        return self.parser.parse_file(file_path, file_source, response_type)
