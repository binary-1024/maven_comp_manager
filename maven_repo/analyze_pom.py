import os
import csv
import json
import subprocess
import re
from utils import My_logger

logger = My_logger(logger_name="analyze_maven_dependencies").get_logger()

def analyze_maven_dependencies(project_dir=None, pom_file_path=None):
    """
    分析 Maven 项目的依赖关系
    Args:
        project_dir: Maven 项目的根目录路径
    Returns:
        包含依赖信息的字典列表，每个字典包含 group_id, artifact_id, version 和 scope
    """
    # 确保目录存在
    if not project_dir:
        if not pom_file_path:
            raise FileNotFoundError(f"项目目录和pom文件路径都不存在: {project_dir}")
                
    # 确保目录中存在 pom.xml
    if project_dir and not os.path.exists(os.path.join(project_dir, "pom.xml")):
        raise FileNotFoundError(f"在目录 {project_dir} 中未找到 pom.xml 文件")
    
    if not os.path.exists(pom_file_path):
        raise FileNotFoundError(f"pom文件路径不存在: {pom_file_path}")
    
    # 执行 mvn dependency:list 命令
    try:
        if project_dir:
            result = subprocess.run(
                ["mvn", "dependency:list"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
        else:
            result = subprocess.run(
                ["mvn", "dependency:list", "-f", pom_file_path],
                capture_output=True,
                text=True,
                check=True
            )
    except subprocess.CalledProcessError as e:
        raise Exception(f"执行 mvn dependency:list 命令失败: {str(e)}")
    
    # 解析输出
    dependencies = []
    # Maven 依赖的正则表达式模式
    pattern = r'\s*([\w\.-]+):([\w\.-]+):([\w\.-]+):([\w\.-]+):(\w+)(?::([\w\.-]+))?'
    #  group_id:artifactId:version:scope
     
        
    
    for line in result.stdout.split('\n'):
        try:
            match = re.search(pattern, line)
            
            if match:
                dependency = {
                    'group_id': match.group(1),
                    'artifact_id': match.group(2),
                    'version': match.group(4),
                    'scope': match.group(5)
                }
                dependencies.append(dependency)
        except Exception as e:
            logger.error(f"resoving dependency error for line: {line}")
            logger.error(f"error: {str(e)}")
            continue

        
    
    return dependencies

def save_dependencies_to_json(dependencies, output_file):
    """
    将依赖信息保存为 JSON 文件
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dependencies, f, indent=2, ensure_ascii=False)

def analyze_and_save_dependencies(project_dir, db_config):
    """
    分析Maven项目依赖并保存到数据库
    
    Args:
        project_dir: Maven项目目录
        db_config: 数据库配置字典，包含 host, user, password, database
    """
    try:
        # 分析依赖
        dependencies = analyze_maven_dependencies(project_dir)
        
        # 保存到数据库
        db = MavenDependencyDB(**db_config)
        db.create_tables()  # 确保表存在
        db.save_dependencies(project_dir, dependencies)
        
        return dependencies
    except Exception as e:
        logger.error(f"分析并保存依赖信息时发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    # 示例用法
    db_config = {
        'host': 'localhost',
        'user': 'your_username',
        'password': 'your_password',
        'database': 'maven_dependencies'
    }
    
    project_dir = input("请输入Maven项目目录路径: ")
    
    try:
        # 分析并保存依赖
        deps = analyze_and_save_dependencies(project_dir, db_config)
        print(f"成功分析并保存了 {len(deps)} 个依赖项")
        
        # 示例：搜索特定依赖
        db = MavenDependencyDB(**db_config)
        spring_deps = db.search_dependencies(group_id='org.springframework')
        print("\n使用Spring框架的项目:")
        for dep in spring_deps:
            print(f"项目: {dep['project_path']}")
            print(f"组件: {dep['group_id']}:{dep['artifact_id']}:{dep['version']}")
            print("---")
            
    except Exception as e:
        print(f"错误: {str(e)}")

