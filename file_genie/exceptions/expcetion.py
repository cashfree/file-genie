class FileParserException(Exception):
    """Base exception for file parser errors."""
    title = "UNKNOWN_ERROR"
    code = 520

    def __init__(self, message="An unknown error occurred"):
        super().__init__(message)
        self.message = message

class ConfigMissingException(FileParserException):
    """Raised when configuration is missing."""
    title = "CONFIG_EXCEPTION"
    code = 500

    def __init__(self, message="Configuration is missing"):
        super().__init__(message)


class FileProcessFailException(FileParserException):
    """Raised when file processing fails."""
    
    def __init__(self, message="File processing failed"):
        super().__init__(message)


class FileReadException(FileParserException):
    """Raised when file reading fails."""
    
    def __init__(self, message="File reading error occurred"):
        super().__init__(message)


class ResourceNotFoundException(FileParserException):
    """Raised when a resource is not found."""
    title = "NOT_FOUND"
    code = 404

    def __init__(self, message="Requested resource not found"):
        super().__init__(message)


class S3Exception(FileParserException):
    """Raised for S3-related issues."""
    title = "S3_EXCEPTION"
    code = 500

    def __init__(self, message="An S3 error occurred"):
        super().__init__(message)

class MissingResourceException(Exception):
    """Exception raised when a required resource is missing, such as configuration or file source."""
    
    def __init__(self, resource_name, message="Required resource is missing"):
        self.resource_name = resource_name
        self.message = f"{message}: {resource_name}"
        super().__init__(self.message)

class NoTemplateFoundForFile(FileParserException):
    """Raised when no template is found."""
    
    def __init__(self, message="No template found for processing"):
        super().__init__(message)
