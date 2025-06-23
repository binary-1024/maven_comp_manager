import os
import sys
import base64
import hashlib
from typing import List, Dict
import json
import ast
# 找到根目录 不可以设置, 因为循环调用了好像....
# parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.append(parent_dir)
# from utils import My_logger
# logger = My_logger(logger_name="commons").get_logger()

## 返回操作系统类型
def get_os_type():
    '''
    得到操作系统，'Linux/Unix' 或者 'Windows' 否则 'Unknown'
    '''
    if os.name == 'posix':
        print("Linux/Unix environtment detected")
        return 'Linux/Unix'
    elif os.name == 'nt':
        print("Windows environtment detected")
        return 'Windows'
    else:
        print("Unknown OS environment detected")
        return 'Unknown'

def encode_base64(data: str) -> str:
    """
    将字符串编码为base64
    
    Args:
        data: 要编码的字符串
    
    Returns:
        base64编码后的字符串
    """
    # 将字符串转换为bytes并编码
    bytes_data = data.encode('utf-8')
    base64_bytes = base64.b64encode(bytes_data)
    # 将bytes转回字符串
    return base64_bytes.decode('utf-8')

def decode_base64(base64_str: str) -> str:
    """
    将base64字符串解码为原始字符串
    Args:
        base64_str: base64编码的字符串
    Returns:
        解码后的原始字符串
    """
    # 解码base64
    bytes_data = base64.b64decode(base64_str)
    # 将bytes转换为字符串
    return bytes_data.decode('utf-8')

def str_to_list_dict(str_data: str):
    """
    将字符串形式的列表字典转换为 list[dict] 类型
    Args:
        str_data: 字符串形式的列表字典
    Returns:
        list[dict]: 转换后的数据
    """
    try:
        # 基本上尝试 3 次解析
        tmp = str_data
        for i in range(3):
            tmp = ast.literal_eval(tmp)
            if type(tmp) == dict or type(tmp) == list:
                return tmp
    except Exception as e:
        print(f"[-] str_to_list_dict error: {e}")
    raise ValueError(f"无法解析字符串: {str_data}")

def generate_md5(data, encoding = 'utf-8'):
    '''
    生成md5哈希值
    Args:
        data: 要生成md5的字符串
        encoding: 编码方式, 默认utf-8
    Returns:
        MD5哈希值(32位小写十六进制字符串)
    '''
    if isinstance(data, str):
        data = data.encode(encoding)
    elif isinstance(data, bytes):
        data = str(data).encode(encoding)
    else:
        raise ValueError("Input data must be a string or bytes")
    
    return hashlib.md5(data).hexdigest()

def collect_json_files(directory: str) -> List[str]:
    """
    搜集目录下所有的JSON文件路径
    Args:
        directory: 要搜索的目录路径 
    Returns:
        List[str]: JSON文件路径列表
    """
    
    json_files = []
    # 使用 os.walk 遍历目录
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                # 构建完整文件路径
                file_path = os.path.join(root, file)
                json_files.append(file_path)
    return json_files

# 按照线程数进行分组
def distribute_files(task_list, num_threads):
    for i in range(num_threads):
        yield task_list[i::num_threads]