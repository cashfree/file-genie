import json_logging, logging, sys
import psutil
from ..enums.LogLevel import LogLevel
from psutil._common import bytes2human

class CustomLogger:
    def __init__(self):
        json_logging.ENABLE_JSON_LOGGING = True
        json_logging.init_non_web()
        self._logger = logging.getLogger("fileparser-logger")
        if not self._logger.handlers:
            self._logger.setLevel(logging.INFO)
            self._logger.addHandler(logging.StreamHandler(sys.stdout))
    
    def print_log(self, log_level=LogLevel.INFO.value, prefix='', message='', postfix='', exc_info=False):
        try:
            prefix=str(prefix)
            message=str(message)
            postfix=str(postfix)
            postfix = postfix + " memory usage :: " + str(bytes2human(psutil.virtual_memory().used))      
            if log_level == LogLevel.INFO.value:
                self._logger.info(prefix+" :: "+message+" :: " +
                            postfix, exc_info=exc_info)
            elif log_level == LogLevel.WARNING.value:
                self._logger.warning(prefix+" :: "+message+" :: " +
                            postfix, exc_info=exc_info)
            elif log_level == LogLevel.WARN.value:
                self._logger.warn(prefix+" :: "+message+" :: " +
                            postfix, exc_info=exc_info)
            elif log_level == LogLevel.ERROR.value:
                self._logger.error(prefix+" :: "+message+" :: " +
                            postfix, exc_info=exc_info)
            elif log_level == LogLevel.EXCEPTION.value:
                self._logger.exception(prefix+" :: "+message+" :: " +
                                postfix, exc_info=exc_info)
            elif log_level == LogLevel.DEBUG.value:
                self._logger.debug(prefix+" :: "+message+" :: " +
                            postfix, exc_info=exc_info)
            elif log_level == LogLevel.CRITICAL.value:
                self._logger.critical(prefix+" :: "+message+" :: " +
                                postfix, exc_info=exc_info)
        except Exception as e:
            self._logger.exception("print_log :: Exception while printing log :: "+str(e))
