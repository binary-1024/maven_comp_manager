import os
from datetime import datetime

####################################################################
# ---- 项目设置的时候必须设置的变量 --------------------------------
####################################################################

## 设置 java 引擎版本, 更新java分析器版本的时候, 如果无特殊情况更新这个版本号就好
JAVA_ENGINE_VERSION = "1.12"
## 设置 data 的目录, 默认是当前目录的兄弟目录
OUT_DATA_ROOT_DIR = os.path.join(os.path.dirname(os.getcwd()),"data")
os.makedirs(OUT_DATA_ROOT_DIR, exist_ok="True")
IN_DATA_ROOT_DIR = os.path.join(os.getcwd(),"data")
os.makedirs(IN_DATA_ROOT_DIR, exist_ok="True")
## 设置日期, 如果我想覆盖掉全局变量我可以在局部自己声明, 也可以在运行程序的时候动态修改
CURRENT_DATE = datetime.now().strftime("%Y%m%d") # 20241122
CURRENT_TIME = datetime.now().strftime("%H%M") # 1059
# CURRENT_DATE_TIME = datetime.now().strftime("%Y%m%d-%H%M") # 20241122-0135
# ---- 项目设置的时候必须设置的变量 END -----------------------------

####################################################################
# 各个模块需要用到的目录, 我是通过参数传递呢 还是通过全局变量直接读取呢...
####################################################################
# ---- java 引擎目录 ----------------------------------------------
CALL_GRAPH_DIR = os.path.join(os.getcwd(),"call_graph")
JAVA_ENGINE_DIR = os.path.join(CALL_GRAPH_DIR,"java_engine")
JAVA_ENGINE_NAME = f"ReachableAnalyzer-{JAVA_ENGINE_VERSION}.jar"
JAVA_ENGINE_PATH = os.path.join(JAVA_ENGINE_DIR, JAVA_ENGINE_NAME)
# ---- java 引擎目录 END -------------------------------------------

# ---- 组件相关 -------------------
## 存储 maven 组件 .jar/source.jar 的根目录
MAVEN_COMP_DIR = os.path.join(OUT_DATA_ROOT_DIR, 'maven_comp_dir')
os.makedirs(MAVEN_COMP_DIR, exist_ok=True)
## 存储 ghsa (github security advisory)的根目录
ADVASIROY_BASE = os.path.join(IN_DATA_ROOT_DIR, "advisories")
os.makedirs(ADVASIROY_BASE, exist_ok=True)
## 存储 组件版本信息
# /Users/mbpr-m4/WorkSpace/sectrend/reachability_front/data/maven_version_dir-html
MAVEN_VERSION_DIR = os.path.join(IN_DATA_ROOT_DIR, 'maven_version_dir')
MAVEN_VERSION_DIR_DATE_ODR = os.path.join(IN_DATA_ROOT_DIR, 'maven_version_dir-html')
MAVEN_VERSION_DIR_NORMAL = os.path.join(IN_DATA_ROOT_DIR, 'maven_version_dir-xml')

os.makedirs(MAVEN_COMP_DIR, exist_ok=True)
## 记录已经在库的组件信息的文件, 这种根目录不需要自动按照日期生成
MAVEN_REPOSITORY_INFO_DIR = os.path.join(os.getcwd(), 'data', 'maven_repository_info')
os.makedirs(MAVEN_REPOSITORY_INFO_DIR, exist_ok=True)
## 记录 KB中已有的 CVE
CVE_COMP_IN_KB_DIR = os.path.join(os.getcwd(), 'data', "cve_comp_in_kb")
os.makedirs(CVE_COMP_IN_KB_DIR, exist_ok=True)
# 维护仓库地址的表格
MAPPING_TABLE_PATH = os.path.join(MAVEN_REPOSITORY_INFO_DIR, "project_repository_mapping_table.json")
# 维护 diff 仓库地址的表格
DIFF_TABLE_PATH = os.path.join(MAVEN_REPOSITORY_INFO_DIR, "diff_repository.json")

# ---- log 相关 -------------------
## 存储 所有的 log 相关
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
## 对于 log 来说是需要按照时间自动生成新的目录的
TODAY_LOG_DIR = os.path.join(LOG_DIR, CURRENT_DATE)
CURRENT_LOG_DIR = os.path.join(TODAY_LOG_DIR, CURRENT_TIME)
os.makedirs(CURRENT_LOG_DIR, exist_ok=True)

# ---- diff 相关 -------------------
#####


####################################################################
# 一些具体的变量值 ###
####################################################################

MAVEN_REPO_LIST = [
            "https://repo1.maven.org/maven2",
            "https://repo.jenkins-ci.org/releases",
            "https://maven.xwiki.org/releases",
            "http://nexus.lizhaoweb.net/content/repositories/releases",
            "https://maven.geo-solutions.it",
            "https://repository.hazelcast.com/release",
            "https://repo.gradle.org/gradle/libs-releases",
            "https://gitblit.github.io/gitblit-maven",
            "https://repository.mulesoft.org/releases",
            "https://maven.restlet.talend.com",
            "https://sig-repo.synopsys.com/bds-integrations-release",
            "https://plugins.gradle.org/m2",
            "https://repository.jboss.org/nexus/content/repositories/public",
            "https://repo.osgeo.org/repository/Geoserver-releases",
            "https://maven.xwiki.org/releases",
            "https://maven.repository.redhat.com/ga",
            "https://www.silverpeas.org/nexus/content/repositories/public",
            "https://repo.akka.io/maven",
            "https://nexus.magnolia-cms.com/content/repositories/magnolia.public.releases",
            "https://repo.opennms.org/maven2",
            "https://repo.osgeo.org/repository/geotools-releases",
            "https://repo.clojars.org",
            "https://maven.wocommunity.org/content/repositories/releases",
            "https://hyperledger.jfrog.io/artifactory/besu-maven",
            "http://4thline.org/m2",
            "https://maven.google.com",
            "https://repository.fit2cloud.com/content/groups/public",
            "https://jitpack.io",
            "https://maven.scijava.org/content/repositories/releases",
            "https://maven.willbl.dev/releases",
            "https://repository.folio.org/repository/maven-folio",
            "https://artifactory.openpreservation.org/artifactory/vera-dev",
            "https://nexus.xwikisas.com/nexus/content/repositories/public-store-releases",
            "https://maven.reposilite.com/releases",
            "https://openhab.jfrog.io/artifactory/libs-release",
            "https://nexus.payara.fish/repository/payara-artifacts",
            "https://nexus.intranda.com/repository/maven-releases",
            "https://nexus.xwiki.com/nexus/content/repositories/public-store-releases",
            "https://repo.thingsboard.io/artifactory/libs-release-public",
            "https://e-contract.be/maven2",
            "https://maven-eu.nuxeo.org/nexus/content/repositories/public-releases",
            "https://dist.wso2.org/maven2",
            "https://repo.softmotions.com/repository/softmotions-public",
            "https://netflixoss.jfrog.io/artifactory/spinnaker",
            "https://repo.opencollab.dev/maven-releases"
        ]

ARTIFACT_ID_DOC_LIST = [
    "https://openhab.jfrog.io/artifactory/libs-release"
]
ARTIFACT_ID_ESCAPE_LIST = [
    "https://repository.fit2cloud.com/content/repository/public"
]
# /Users/mbpr-m4/WorkSpace/sectrend/reachability_front/utils/stealth.min.js
STEALTH_PATH = os.path.join(os.getcwd(), "utils", "stealth.min.js")

GITHUB_TOKEN_LIST = [
    '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',
    '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',
    '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',
    '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',
    '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',
    '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',
    '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',
    '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',
    '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',
    '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'
]

DB_CONFIG = {
    'host': '192.168.9.128',
    'port': '13307',
    'user': 'root',
    'password': 'Sectrend@!23',
    'database': 'monitored_issues_db',
    'raise_on_warnings': True
}