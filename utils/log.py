import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
from global_var_setting import LOG_DIR
import colorlog

class My_logger:
    '''
    日志记录器
    - logger_name: 设置日志名,默认是 default
    - logger_dir: 设置日志基本目录 
    '''
    def __init__(self, logger_dir: str = None, logger_name: str = "default", logger_level=logging.DEBUG):
        # 定义日志目录
        date = datetime.now().strftime("%Y%m%d")
        time = datetime.now().strftime("%H%M")
        logger_dir = LOG_DIR if logger_dir is None else logger_dir
        self.logger_dir = os.path.join(logger_dir, date, time)
        os.makedirs(self.logger_dir, exist_ok=True)
        # 定义日志名
        self.logger_name = logger_name
        # 这个如果没有指定名字的 logger 则返回rootLogger
        self.logger = logging.getLogger(self.logger_name)
        # 定义 logger 的 level
        self.logger_level = logger_level
        # 定义日志级别, 默认是 DEBUG, 如果需要修改调用 set_logger_level 方法
        self.logger.setLevel(logger_level)
        # 初始化对象
        self.setup_logger(logger_name)
        self.add_console_handler()

    def get_logger(self):
        '''
        返回日志对象
        '''
        return self.logger

    def setup_logger(self, log_name: str):
        # 设置日志文件相关信息
        if not self.logger.handlers:
            self._add_file_handler(log_name, logging.DEBUG, 'debug')
            self._add_file_handler(log_name, logging.INFO, 'record')
            self._add_file_handler(log_name, logging.WARNING, 'warning')
            self._add_file_handler(log_name, logging.ERROR, 'errors')
        else:
            pass
            # print(f"logger {self.logger_name} already exists")

    def _add_file_handler(self, log_name: str, level: int, suffix: str):
        '''
        - 
        '''
        # 默认设置日志大小为 10MB, 备份 10 个, 命名会在后面加 .log.1, .log.2 ...
        file_handler = RotatingFileHandler(
            os.path.join(self.logger_dir, f'{log_name}_{suffix}.log'),
            # os.path.join(self.logger_dir, f'{suffix}.log'),
            maxBytes=10*1024*1024,
            backupCount=10
        )
        file_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def add_console_handler(self):
        if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
            console_handler = logging.StreamHandler()
            # 如果希望只展示 warning 或者 error 就设置 warning 或者 error
            # 如果希望连 info 都展示出来 那就将他设置为 DEBUG 这个就可以了
            console_handler.setLevel(logging.INFO)
            formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def set_logger_level(self, level: int = logging.DEBUG):
        self.logger.setLevel(level)


# basic_logger = My_logger(LOG_DIR, 'basic_logger')
# basic_logger = My_logger(LOG_DIR, 'basic_logger')
# basic_logger.setup_logger('basic_logger')
# basic_logger.add_console_handler()
# logger = basic_logger.get_logger()

if __name__ == "__main__":
    # test
    logger = My_logger().get_logger()