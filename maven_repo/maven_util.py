import os
import json
import csv
import sys
import requests
import xml.etree.ElementTree as ET
from io import BytesIO
import time
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
from tqdm import tqdm
from utils import My_logger
from global_var_setting import MAPPING_TABLE_PATH, MAVEN_VERSION_DIR_DATE_ODR,MAVEN_VERSION_DIR,MAVEN_VERSION_DIR_NORMAL, DIFF_TABLE_PATH, ARTIFACT_ID_ESCAPE_LIST, ARTIFACT_ID_DOC_LIST,MAVEN_REPO_LIST, STEALTH_PATH
logger = My_logger(logger_name="maven_repo").get_logger()

from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Tuple
from playwright.sync_api import sync_playwright
# from DrissionPage import Chromium, ChromiumOptions, SessionPage
from urllib.parse import quote
import time
import random


class MavenRepo:
    def __init__(self, group_id, artifact_id):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.url_prefix = "https://mvnrepository.com/artifact"
        self.url_download_prefix = "https://repo1.maven.org/maven2"
        self.versions = None
        self.meta_url = None
        self.html_url = f"{self.url_prefix}/{self.group_id}/{self.artifact_id}"
        self.url_download_candidates = MAVEN_REPO_LIST
    
    def gen_url_from_ga(self):
        '''生成可访问的 maven-metadata.xml 的 url
        - 需要 self.group_id, self.artifact_id, self.url_download_prefix 不为空
        '''
        # 检查参数是否为空
        if not all([self.group_id, self.artifact_id, self.url_download_prefix]):
            logger.error(f"Error: group_id, artifact_id, url_download_prefix cannot be None")
            return None
        # 检查生成 url 是否需要 escape
        if self.artifact_id in ARTIFACT_ID_ESCAPE_LIST:
            new_item2 = f"{self.group_id.replace('.', '%2F')}/{self.artifact_id.replace('.', '%2F')}"
        else:
            new_item2 = f"{self.group_id.replace('.', '/')}/{self.artifact_id}"
        self.meta_url = f"{self.url_download_prefix}/{new_item2}/maven-metadata.xml"
        logger.info(f"[+] gen_url_from_ga done, {self.meta_url}")
        return self.meta_url
    
    def get_correct_ga_info(self):
        '''
        获取正确的 ga 信息
        '''
        with open(DIFF_TABLE_PATH, 'r', encoding='utf-8') as f:
            diff_repository_data = json.load(f)
        ga_key = f"{self.group_id}:{self.artifact_id}"
        if ga_key in diff_repository_data.keys():
            item = diff_repository_data[ga_key]
            if item["label"] == "ga_diff":
                group_id_list = item.get("group_id", [])
                group_id_list = group_id_list if group_id_list != [] else [self.group_id]
                artifact_id_list = item.get("artifact_id", [])
                artifact_id_list = artifact_id_list if artifact_id_list != [] else [self.artifact_id]
                if group_id_list == [] and artifact_id_list == []:
                    return None
                # 如果 group_id 存在, 那么做一个笛卡尔积一个一个试
                all_ga_list = [(x, y) for x in group_id_list for y in artifact_id_list]
                url_prefix = item.get("repository", self.url_download_prefix)
                self.url_download_prefix = url_prefix
                return all_ga_list
        return None

    # 外部函数 加锁
    def search_repository_prefix(self, artifact_key, file_lock=None):
        logger.info(f"[+] search_repository_prefix for {artifact_key}")
        # 如果 file_lock 存在 则使用 file_lock 进行加锁
        repository_prefix = []
        if file_lock is not None:
            with file_lock:
                repository_prefix = self._search_repository_prefix(artifact_key)
        else:
            repository_prefix = self._search_repository_prefix(artifact_key)
        return repository_prefix  

    # 内部函数 不加锁
    def _search_repository_prefix(self,artifact_key):
        # 读取 mapping table
        with open(MAPPING_TABLE_PATH, 'r', encoding='utf-8') as f:
            mapping_table = json.load(f)
        # 如果 artifact key 存在 则返回 artifact key 对应的 repository 前缀
        if artifact_key in mapping_table.keys():
            logger.info(f"[+] artifact_key: {artifact_key} found in mapping_table")
            return mapping_table[artifact_key]
        logger.info(f"[-] artifact_key: {artifact_key} not found in mapping_table")
        return None
    
################# -------- end ------------ #################

        



if __name__ == "__main__":
    pass