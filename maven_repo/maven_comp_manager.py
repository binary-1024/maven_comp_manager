class MavenComponentManager:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def add_component(self, group_id, artifact_id, repo_platform="Maven", description=None):
        """添加新组件"""
        cursor = self.db.cursor()
        try:
            sql = """
                INSERT INTO components (group_id, artifact_id, repo_platform, description) 
                VALUES (%s, %s, %s, %s)
                AS new_values
                ON DUPLICATE KEY UPDATE 
                    description = COALESCE(new_values.description, description),
                    repo_platform = COALESCE(new_values.repo_platform, repo_platform)
            """
            cursor.execute(sql, (group_id, artifact_id, repo_platform, description))
            self.db.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
    
    def add_repository(self, repo_url, repo_name=None, repo_type="OTHER", repo_prefix=None, status=True, priority=0):
        """添加新仓库"""
        cursor = self.db.cursor()
        try:
            sql = """
                INSERT INTO repositories (repo_url, repo_name, repo_type, repo_prefix, status, priority)
                VALUES (%s, %s, %s, %s, %s, %s)
                AS new_values
                ON DUPLICATE KEY UPDATE
                    repo_name = COALESCE(new_values.repo_name, repo_name),
                    repo_type = COALESCE(new_values.repo_type, repo_type),
                    repo_prefix = COALESCE(new_values.repo_prefix, repo_prefix),
                    status = COALESCE(new_values.status, status),
                    priority = COALESCE(new_values.priority, priority)
            """
            cursor.execute(sql, (repo_url, repo_name, repo_type, repo_prefix, status, priority))
            self.db.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
    
    def construct_download_url(self, group_id, artifact_id, version, repo_url):
        return f"{repo_url.rstrip('/')}/{group_id.replace('.', '/')}/{artifact_id}/{version}"
    
    def add_component_version(self, group_id, artifact_id, version, repo_url, 
                              jar_available=False, src_available=False):
        """添加组件版本"""
        cursor = self.db.cursor()
        try:
            # 获取或创建组件
            comp_sql = "SELECT id FROM components WHERE group_id = %s AND artifact_id = %s AND version = %s"
            cursor.execute(comp_sql, (group_id, artifact_id, version))
            result = cursor.fetchone()
            if not result:
                # 创建组件
                comp_id = self.add_component(group_id, artifact_id, version)
            else:
                comp_id = result[0]
            
            # 获取或创建仓库
            repo_sql = "SELECT id FROM repositories WHERE repo_url = %s"
            cursor.execute(repo_sql, (repo_url,))
            result = cursor.fetchone()
            if not result:
                # 创建仓库
                repo_id = self.add_repository(repo_url)
            else:
                repo_id = result[0]
                
            # 构建下载URL
            download_url = self.construct_download_url(group_id, artifact_id, version, repo_url)
            pom_url = f"{download_url}/{artifact_id}-{version}.pom"
            jar_url = f"{download_url}/{artifact_id}-{version}.jar"
            # src_url = f"{download_url}/{artifact_id}-{version}-sources.jar"
            
            # 添加版本信息
            version_sql = """
                INSERT INTO component_versions 
                (component_id, version, repository_id, download_url, pom_url, 
                jar_available, src_available, last_checked)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                AS new_values
                ON DUPLICATE KEY UPDATE
                    download_url = new_values.download_url,
                    jar_available = new_values.jar_available,
                    src_available = new_values.src_available,
                    pom_url = new_values.pom_url,
                    last_checked = NOW()
            """
            cursor.execute(version_sql, (
                comp_id, version, repo_id, download_url, pom_url, 
                jar_available, src_available
            ))
            self.db.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            
    def find_all_versions(self, group_id, artifact_id):
        """查找组件的所有版本（跨所有仓库）"""
        cursor = self.db.cursor(dictionary=True)
        try:
            sql = """
                SELECT cv.version, r.repo_url, r.repo_name, 
                       cv.jar_available, cv.src_available, cv.last_checked
                FROM components c
                JOIN component_versions cv ON c.id = cv.component_id
                JOIN repositories r ON cv.repository_id = r.id
                WHERE c.group_id = %s AND c.artifact_id = %s
                ORDER BY r.priority DESC, cv.version DESC
            """
            cursor.execute(sql, (group_id, artifact_id))
            return cursor.fetchall()
        finally:
            cursor.close()
            
    def find_best_repository(self, group_id, artifact_id, version):
        """查找特定版本的最佳可用仓库"""
        cursor = self.db.cursor(dictionary=True)
        try:
            sql = """
                SELECT r.repo_url, r.repo_name, cv.download_url, 
                       cv.jar_available, cv.src_available
                FROM components c
                JOIN component_versions cv ON c.id = cv.component_id
                JOIN repositories r ON cv.repository_id = r.id
                WHERE c.group_id = %s AND c.artifact_id = %s AND cv.version = %s
                      AND r.status = TRUE
                ORDER BY cv.jar_available DESC, r.priority DESC
                LIMIT 1
            """
            cursor.execute(sql, (group_id, artifact_id, version))
            return cursor.fetchone()
        finally:
            cursor.close()