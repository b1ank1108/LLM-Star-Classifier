import sqlite3
import json
from datetime import datetime, timedelta
import os

class DatabaseError(Exception):
    """数据库操作异常基类"""
    pass

class Database:
    def __init__(self, db_path='stars.db'):
        self.db_path = db_path
        try:
            self.init_db()
        except Exception as e:
            raise DatabaseError(f"初始化数据库失败: {str(e)}")

    def init_db(self):
        """初始化数据库，创建必要的表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建仓库表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS repositories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        description TEXT,
                        language TEXT,
                        topics TEXT,
                        url TEXT,
                        readme TEXT,
                        category TEXT,
                        ai_summary TEXT,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                ''')
                
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"创建数据库表失败: {str(e)}")

    def repo_exists(self, repo_name):
        """检查仓库是否已存在"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM repositories WHERE name = ?', (repo_name,))
                return cursor.fetchone()[0] > 0
        except sqlite3.Error as e:
            raise DatabaseError(f"检查仓库是否存在失败: {str(e)}")

    def save_repo(self, repo_data):
        """保存或更新仓库信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 将topics列表转换为JSON字符串
                topics_json = json.dumps(repo_data['topics'], ensure_ascii=False)
                
                # 检查仓库是否存在
                if self.repo_exists(repo_data['name']):
                    # 更新现有记录
                    cursor.execute('''
                        UPDATE repositories 
                        SET description = ?, language = ?, topics = ?, url = ?, readme = ?, updated_at = ?
                        WHERE name = ?
                    ''', (
                        repo_data['description'],
                        repo_data['language'],
                        topics_json,
                        repo_data['url'],
                        repo_data['readme'],
                        datetime.now(),
                        repo_data['name']
                    ))
                else:
                    # 插入新记录
                    cursor.execute('''
                        INSERT INTO repositories 
                        (name, description, language, topics, url, readme, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        repo_data['name'],
                        repo_data['description'],
                        repo_data['language'],
                        topics_json,
                        repo_data['url'],
                        repo_data['readme'],
                        datetime.now(),
                        datetime.now()
                    ))
                
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"保存仓库信息失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise DatabaseError(f"JSON序列化失败: {str(e)}")

    def get_all_repos(self):
        """获取所有仓库信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM repositories')
                columns = [description[0] for description in cursor.description]
                repos = []
                
                for row in cursor.fetchall():
                    repo = dict(zip(columns, row))
                    try:
                        # 将JSON字符串转换回列表
                        repo['topics'] = json.loads(repo['topics'])
                    except json.JSONDecodeError:
                        repo['topics'] = []
                    repos.append(repo)
                
                return repos
        except sqlite3.Error as e:
            raise DatabaseError(f"获取仓库列表失败: {str(e)}")

    def update_repo_category(self, repo_name, category):
        """更新仓库的分类"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE repositories 
                    SET category = ?, updated_at = ?
                    WHERE name = ?
                ''', (category, datetime.now(), repo_name))
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"更新仓库分类失败: {str(e)}")

    def update_repo_summary(self, repo_name, summary):
        """更新仓库的AI总结"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE repositories 
                    SET ai_summary = ?, updated_at = ?
                    WHERE name = ?
                ''', (summary, datetime.now(), repo_name))
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"更新仓库总结失败: {str(e)}")

    def get_repos_by_category(self, category):
        """获取指定分类的所有仓库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM repositories WHERE category = ?', (category,))
                columns = [description[0] for description in cursor.description]
                repos = []
                
                for row in cursor.fetchall():
                    repo = dict(zip(columns, row))
                    try:
                        repo['topics'] = json.loads(repo['topics'])
                    except json.JSONDecodeError:
                        repo['topics'] = []
                    repos.append(repo)
                
                return repos
        except sqlite3.Error as e:
            raise DatabaseError(f"获取分类仓库失败: {str(e)}")

    def delete_repos_not_updated_since(self, timestamp, threshold_days=7):
        """删除在指定时间之前更新的仓库
        
        Args:
            timestamp: datetime对象，表示时间点
            threshold_days: int，删除超过多少天未更新的仓库
        
        Returns:
            tuple: (deleted_count, skipped_count) 删除的仓库数量和跳过的仓库数量
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 首先获取可能要删除的仓库数量
                cursor.execute('''
                    SELECT COUNT(*) FROM repositories 
                    WHERE updated_at < ?
                ''', (timestamp,))
                total_outdated = cursor.fetchone()[0]
                
                # 计算阈值时间
                threshold_time = timestamp - timedelta(days=threshold_days)
                
                # 删除超过阈值时间的仓库
                cursor.execute('''
                    DELETE FROM repositories 
                    WHERE updated_at < ?
                ''', (threshold_time,))
                deleted_count = cursor.rowcount
                
                conn.commit()
                return deleted_count, total_outdated - deleted_count
        except sqlite3.Error as e:
            raise DatabaseError(f"删除旧仓库失败: {str(e)}") 