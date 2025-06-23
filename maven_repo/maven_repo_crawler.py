import os
import json
import csv
import sys
import requests
import time
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
from tqdm import tqdm
from utils import My_logger
from global_var_setting import MAPPING_TABLE_PATH, MAVEN_VERSION_DIR_DATE_ODR,MAVEN_VERSION_DIR,MAVEN_VERSION_DIR_NORMAL, DIFF_TABLE_PATH, ARTIFACT_ID_ESCAPE_LIST, ARTIFACT_ID_DOC_LIST,MAVEN_REPO_LIST, STEALTH_PATH
logger = My_logger(logger_name="maven_repo_crawler").get_logger()



class MavenRepositoryCrawler:
    def __init__(self, group_id, artifact_id):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.url_prefix = "https://mvnrepository.com/artifact"
        self.url_download_prefix = "https://repo1.maven.org/maven2"
        self.versions = None
        self.meta_url = None
        self.html_url = f"{self.url_prefix}/{self.group_id}/{self.artifact_id}"
        self.url_download_candidates = MAVEN_REPO_LIST
    

    def set_gav(self, group_id, artifact_id):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.html_url = f"{self.url_prefix}/{self.group_id}/{self.artifact_id}"
        self.url_download_candidates = MAVEN_REPO_LIST


    def crawl_central_maven(self, group_id, artifact_id):
        """爬取Maven中央仓库的组件版本"""
        repo_url = "https://repo1.maven.org/maven2"
        versions = self._fetch_versions_from_central(group_id, artifact_id)
        
        for version in versions:
            # 检查JAR和源码是否可用
            jar_available = self._check_jar_availability(repo_url, group_id, artifact_id, version)
            src_available = self._check_source_availability(repo_url, group_id, artifact_id, version)
            
            # 添加到数据库
            self.manager.add_component_version(
                group_id, artifact_id, version, repo_url,
                jar_available, src_available
            )
            
    def _fetch_versions_from_central(self, group_id, artifact_id):
        """从Maven中央仓库获取版本列表"""
        url = f"https://repo1.maven.org/maven2/{group_id.replace('.', '/')}/{artifact_id}/"
        # 使用requests和BeautifulSoup实现爬取逻辑
        # ...
        
    def _check_jar_availability(self, repo_url, group_id, artifact_id, version):
        """检查JAR文件是否可用"""
        # ...
        
    def _check_source_availability(self, repo_url, group_id, artifact_id, version):
        """检查源码JAR是否可用"""
        # ...