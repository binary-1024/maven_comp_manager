import re
import json
import csv
import os
import sys
from datetime import datetime
from .log import My_logger
from .commons import decode_base64, str_to_list_dict, generate_md5

logger = My_logger(logger_name='data_cleaning').get_logger()


def check_purl_ver_match_risky_func(purl_version, risky_function):
    '''
    检查purl_version与 risky_function中的component中的 gav是否匹配
    '''
    component = risky_function.get("component", None)
    if not component:
        return False
    group_id, artifact_id, version = component.split("/")
    purl_version_ = f"pkg:maven/{group_id}/{artifact_id}@{version}"
    if purl_version == purl_version_:
        return True
    return False


def check_special_class_and_method(class_name: str, method_name: str) -> bool:
    """
    检查是否存在特殊的类和方法（内部类、匿名类、内部方法、匿名方法）
    Args:
        class_name: 类名
        method_name: 方法名
    Returns:
        bool: 是否存在特殊类或方法
    """
    # 匹配模式
    # 后面可以添加别的类型的正则表达式
    patterns = {
        'inner_class_method': r'\$\d+'                    # 内部类/方法, 美元符+一个或多个数字
    }
    
    # 检查类名
    has_special_class = any(
        bool(re.search(pattern, class_name))
        for pattern in [patterns['inner_class_method']]
    )
    
    # 检查方法名
    has_special_method = any(
        bool(re.search(pattern, method_name))
        for pattern in [patterns['inner_class_method']]
    )
    
    return has_special_class or has_special_method

def filter_reachable_data(file_path, from_commit=None):
    cve_info_path = "/Users/macm1/Workspace/test/data/maven_cves_all_info_241224_groupby_cve.json"
    with open(cve_info_path, 'r', encoding='utf-8') as f:
        cve_info = json.load(f)
    counter = 0
    filtered_counter = 0
    dt = None
    output_path = file_path.replace(".csv", "_filtered_250108.csv")
    output_path_cve = file_path.replace(".csv", "_cve_not_matched.csv")
    output_path_purl = file_path.replace(".csv", "_purl_not_matched.csv")
    with open(file_path, 'r', encoding='utf-8') as f, open(output_path, 'w', encoding='utf-8') as f_out, open(output_path_cve, 'w', encoding='utf-8') as f_out_cve, open(output_path_purl, 'w', encoding='utf-8') as f_out_purl:
        reader = csv.reader(f, delimiter='\001')
        writer = csv.writer(f_out, delimiter='\001')
        writer_cve = csv.writer(f_out_cve, delimiter='\001')
        writer_purl = csv.writer(f_out_purl, delimiter='\001')
        for row in reader:
            counter += 1
            if len(row) == 10:
                primary_key, md5_purl_version, purl_version, cve_id, risky_function, risky_function_base64, path, path_base64, from_commit, dt = row
            elif len(row) == 7:
                md5_purl_version, purl_version, cve_id, risky_function, risky_function_base64, path, path_base64 = row
            else:
                logger.error(f"[-] invalid row: {row}")
                continue
                
            purl = purl_version.split("@")[0]
            version = purl_version.split("@")[1]
            try:
                if type(risky_function) != dict:
                    risky_function = decode_base64(risky_function_base64)
                    risky_function = str_to_list_dict(risky_function)
                if type(path) != list and path:
                    path = str_to_list_dict(path)
                if not purl_version.startswith("pkg:maven/"):
                    purl_version = f"pkg:maven/{purl}@{version}"
            except Exception as e:
                logger.error(f"[-] filter_reachable_data error: {e}")
                continue
            primary_key = generate_md5(md5_purl_version+ cve_id+ risky_function_base64)
            dt = datetime.now().strftime('%Y%m%d') if dt is None else dt
            if cve_id in cve_info:
                if purl in cve_info[cve_id]:
                    if version in cve_info[cve_id][purl]:
                        # reachable_data.append(row)
                        writer.writerow([
                            primary_key, md5_purl_version, purl_version, cve_id, risky_function, risky_function_base64, path, path_base64, from_commit, dt
                        ])
                        filtered_counter += 1
                    else:
                        logger.warning(f"[-] [version not matched] {cve_id} {purl} {version} not in cve_info")  
                else:
                    logger.warning(f"[-] [purl not matched] {cve_id} {purl} not in cve_info")
                    writer_purl.writerow([
                        primary_key, md5_purl_version, purl_version, cve_id, risky_function, risky_function_base64, path, path_base64, from_commit, dt
                    ])
            else:
                logger.warning(f"[-] [cve not matched] {cve_id} {purl} not in cve_info")
                writer_cve.writerow([
                    primary_key, md5_purl_version, purl_version, cve_id, risky_function, risky_function_base64, path, path_base64, from_commit, dt
                ])
                continue
    logger.info(f"[+] filter_reachable_data done, collect {filtered_counter}/{counter} rows")

def strip_inner_class_method(input_file_path, delimiter=','):
    counter = 0
    
    output_path = input_file_path.replace(".csv", "_stripped_anonmymous.csv")
    with open(input_file_path, "r", encoding="utf-8") as f, open(output_path, "w", encoding="utf-8") as f2:
        data = csv.reader(f, delimiter=delimiter)
        writer = csv.writer(f2, delimiter=delimiter)
        for item in data:
            purl_version = None
            risky_function = None
            path = None
            if len(item) == 4:
                md5_purl_version, cve_id, risky_function_base64, from_commit = item
            elif len(item) == 8:
                md5_purl_version, cve_id, risky_function_base64, risky_function, path_64, path, from_commit, dt = item
            elif len(item) == 7:
                md5_purl_version, purl_version, cve_id, risky_function, risky_function_base64, path, path_64 = item
            elif len(item) == 10:
                primary_key, md5_purl_version, purl_version, cve_id, risky_function, risky_function_base64, path, path_64, from_commit, dt = item
            else:
                logger.error(f"invalid item elements {item}")
                continue
            # risky_function = ast.literal_eval(risky_function)
            try:
                if type(risky_function) != dict:
                    risky_function = decode_base64(risky_function_base64)
                    risky_function = str_to_list_dict(risky_function)
                if type(path) != list and path:
                    path = str_to_list_dict(path)
            except Exception as e:
                logger.error(f"strip_inner_class_method error: {e}")
                continue

            packageName = risky_function['packageName']
            methodName = risky_function['methodName']
            
            if check_special_class_and_method(packageName, methodName):
                logger.info(f"[-] {packageName} {methodName} is special, pass {md5_purl_version},{cve_id},{risky_function_base64}")
                continue
            # 检查purl_version与 risky_function中的component中的 gav是否匹配
            # if not check_md5_not_match_purl(purl_version, risky_function):
            #     print(f"[-] {purl_version} {risky_function} not match, pass {md5_purl_version},{cve_id},{risky_function_base64}")
            #     continue

            if len(item) == 4:
                writer.writerow(item)
                counter += 1
            else:
                from_commit = "1"
                dt = "20250102"
                new_item = [
                    md5_purl_version, purl_version, cve_id, risky_function_base64, risky_function, path_64, path, from_commit, dt
                ]
                writer.writerow(new_item)
                counter += 1
    logger.info(f"[+] strip_inner_class_method done, collect {counter} rows")
