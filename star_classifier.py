import json
import yaml
import os
import requests
from github import Github
from tqdm import tqdm
from db import Database, DatabaseError
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading
from datetime import datetime

class StarClassifier:
    def __init__(self):
        try:
            # 加载配置
            with open('config.yaml', 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # 创建数据库目录
            db_dir = os.path.dirname(self.config['database']['path'])
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            
            # 初始化GitHub客户端和数据库
            self.github = Github(self.config['github']['token'])
            self.session = requests.Session()
            self.db = Database(self.config['database']['path'])
            self.categories_data = {}
            
            # 初始化线程池和数据库锁
            self.fetch_max_workers = self.config.get('concurrency', {}).get('fetch', {}).get('max_workers', 1)
            self.classify_max_workers = self.config.get('concurrency', {}).get('classify', {}).get('max_workers', 1)
            self.db_lock = threading.Lock()
            self.fetch_executor = ThreadPoolExecutor(max_workers=self.fetch_max_workers)
            self.classify_executor = ThreadPoolExecutor(max_workers=self.classify_max_workers)
            
            # 初始化API key轮询
            self.api_keys = self.config['openai'].get('api_keys', [])
            self.current_api_key_index = 0
            self.api_key_lock = threading.Lock()
            
            if not self.api_keys:
                raise ValueError("未配置OpenAI API keys")
        except Exception as e:
            print(f"初始化失败: {str(e)}")
            raise

    def _get_next_api_key(self):
        """获取下一个API key（线程安全）"""
        with self.api_key_lock:
            api_key = self.api_keys[self.current_api_key_index]
            self.current_api_key_index = (self.current_api_key_index + 1) % len(self.api_keys)
            return api_key

    def _process_single_repo(self, repo):
        """处理单个仓库的辅助方法"""
        try:
            
            repo_data = {
                "name": repo.full_name,
                "description": repo.description or "",
                "language": repo.language or "",
                "topics": repo.get_topics(),
                "url": repo.html_url,
            }
            
            # 获取README内容
            try:
                readme = repo.get_readme()
                content = readme.decoded_content.decode('utf-8')
                repo_data["readme"] = content[:500] # 只取前500字
            except:
                repo_data["readme"] = ""
            
            # 使用锁保护数据库操作
            with self.db_lock:
                # 检查仓库是否存在
                exists = self.db.repo_exists(repo.full_name)
                self.db.save_repo(repo_data)
            return True
        except Exception as e:
            print(f"处理仓库 {repo.full_name} 时出错: {str(e)}")
            return False

    def fetch_starred_repos(self):
        """获取用户star的所有仓库"""
        # TODO 超出rate limit的解决方案
        try:
            # 记录开始更新的时间
            update_start_time = datetime.now()
            
            user = self.github.get_user()
            starred_repos = user.get_starred()
            
            print("\n获取到的Starred仓库列表：")
            print("=" * 80)
            
            # 使用线程池并发处理仓库
            futures = []
            total_repos = 0
            
            # 处理分页列表
            for repo in starred_repos:
                future = self.fetch_executor.submit(self._process_single_repo, repo)
                futures.append(future)
                total_repos += 1
            
            # 等待所有任务完成
            success_count = 0
            for future in tqdm(as_completed(futures), total=total_repos, desc="处理Starred仓库"):
                if future.result():
                    success_count += 1
            
            # 删除未更新的仓库（已取消star的）
            threshold_days = self.config.get('database', {}).get('cleanup', {}).get('threshold_days', 7)
            deleted_count, skipped_count = self.db.delete_repos_not_updated_since(
                update_start_time, 
                threshold_days=threshold_days
            )
            
            print(f"\n成功处理 {success_count}/{total_repos} 个仓库")
            if deleted_count > 0 or skipped_count > 0:
                print(f"发现 {deleted_count + skipped_count} 个未更新的仓库：")
                print(f"- 已删除 {deleted_count} 个超过 {threshold_days} 天未更新的仓库")
                print(f"- 暂时保留 {skipped_count} 个仓库（未超过清理阈值）")
            
        except Exception as e:
            print(f"获取Starred仓库失败: {str(e)}")
            raise

    def _call_openai(self, prompt, response_format="", system_prompt=None):
        """通用的OpenAI API调用方法
        
        Args:
            prompt (str): 用户提示词
            response_format (str): 响应格式，默认为json_object
            system_prompt (str): 系统提示词，可选
        """
        system_prompt = "你只能返回JSON格式数据，不要包含其他内容，不要格式化和markdown包裹"
        try:
            # 构建消息列表
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # 构建请求参数
            payload = {
                "model": self.config['openai'].get('model', 'gpt-3.5-turbo'),
                "stream": False,
                "max_tokens": self.config['openai'].get('max_tokens', 512),
                "temperature": self.config['openai'].get('temperature', 0.7),
                "top_p": self.config['openai'].get('top_p', 0.7),
                "top_k": self.config['openai'].get('top_k', 50),
                "frequency_penalty": self.config['openai'].get('frequency_penalty', 0.5),
                "n": 1,
                "messages": messages
            }
            
            # 如果是JSON响应，添加response_format
            if response_format == "json_object":
                payload["response_format"] = {"type": "json_object"}
            
            # 获取下一个API key
            api_key = self._get_next_api_key()
            
            # 发送请求
            response = self.session.post(
                f"{self.config['openai']['api_base']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 200:
                result = response.text
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            else:
                print(f"API调用失败: {response.status_code}")
                print(f"API调用失败: {response.text}")
                return None
                
        except Exception as e:
            print(f"OpenAI API调用失败: {str(e)}")
            print(f"OpenAI API调用失败: {result}")
            return None

    def classify_repo(self, repo):
        """使用OpenAI API对仓库进行分类和总结，并更新数据库
        
        Args:
            repo (dict): 仓库信息字典
            
        Returns:
            bool: 是否成功处理
        """
        try:
            # 构建提示词
            prompt = f"""
            请根据以下仓库信息，完成分类和总结任务：
            
            仓库名称：{repo['name']}
            描述：{repo['description']}
            语言：{repo['language']}
            主题：{', '.join(repo['topics'])}
            README：{repo['readme']}...
            
            可选的分类类别：{', '.join(self.config['categories'])}
            
            请按照以下JSON格式返回结果，不要markdown包裹：
            {{
                "category": "最合适的类别名称",
                "summary": "50字以内的仓库总结"
            }}
            
            注意：
            1. category必须是以下之一：{', '.join(self.config['categories'])}
            2. summary应该简明扼要地描述仓库的主要功能和特点
            3. 只返回JSON格式数据，不要包含其他内容，不要格式化和markdown包裹
            """
            
            # 调用AI进行分类和总结
            result = self._call_openai(prompt)
            if result:
                category = result.get("category", "其他")
                summary = result.get("summary", "")
                
                # 验证分类是否有效
                if category not in self.config['categories']:
                    category = "其他"
                
                # 使用锁保护数据库操作
                with self.db_lock:
                    self.db.update_repo_category(repo['name'], category)
                    self.db.update_repo_summary(repo['name'], summary)
                
                # 更新分类统计
                if category not in self.categories_data:
                    self.categories_data[category] = []
                self.categories_data[category].append(repo["name"])
                return True
            return False
        except Exception as e:
            print(f"处理仓库 {repo['name']} 时出错: {str(e)}")
            return False

    def classify_all_repos(self, uncategorized_only=False):
        """对所有仓库进行分类
        
        Args:
            uncategorized_only (bool): 是否只处理未分类的仓库
        """
        try:
            # 从数据库获取所有仓库
            repos = self.db.get_all_repos()
            
            # 如果只处理未分类的仓库，进行过滤
            if uncategorized_only:
                repos = [repo for repo in repos if not repo['category'] or repo['category'] == '其他']
                print(f"\n找到 {len(repos)} 个未分类的仓库")
            
            # 使用线程池并发处理仓库
            futures = []
            for repo in repos:
                future = self.classify_executor.submit(self.classify_repo, repo)
                futures.append(future)
            
            # 等待所有任务完成
            success_count = 0
            for future in tqdm(as_completed(futures), total=len(futures), desc="分类仓库"):
                if future.result():
                    success_count += 1
            
            print(f"\n成功处理 {success_count}/{len(repos)} 个仓库")
            
        except DatabaseError as e:
            print(f"获取仓库列表失败: {str(e)}")
            raise
        except Exception as e:
            print(f"分类过程出错: {str(e)}")
            raise

    def generate_categories(self):
        """使用AI分析仓库并生成合适的分类"""
        try:
            # 从数据库获取所有仓库
            repos = self.db.get_all_repos()
            
            # 准备仓库信息用于分析
            repos_info = []
            for repo in repos:
                repos_info.append({
                    "name": repo['name'],
                    "description": repo['description'][:50],
                })
            
            # 构建提示词
            prompt = f"""
            请分析以下GitHub仓库列表，生成5-10个合适的分类类别。每个类别应该：
            1. 具有明确的主题和范围
            2. 能够覆盖多个仓库
            3. 名称简洁明了
            4. 使用中文命名
            
            仓库列表：
            {json.dumps(repos_info, ensure_ascii=False, indent=2)}
            
            请按照以下JSON格式返回结果，不要markdown包裹：
            {{
                "categories": [
                    "分类1",
                    "分类2",
                    ...
                ],
                "category_descriptions": {{
                    "分类1": "该分类的简要说明",
                    "分类2": "该分类的简要说明",
                    ...
                }}
            }}
            
            注意：
            1. 分类名称应该简洁，不超过4个字
            2. 分类说明应该清晰描述该分类的用途和范围
            3. 只返回JSON格式数据，不要包含其他内容，不要格式化和markdown包裹
            """
            
            result = self._call_openai(prompt)
            print(result)
            if result:
                categories = result.get("categories", [])
                descriptions = result.get("category_descriptions", {})
                
                # 更新配置文件
                self.config['categories'] = categories
                with open('config.yaml', 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, allow_unicode=True, sort_keys=False)
                
                # 打印生成的分类
                print("\n生成的分类：")
                print("=" * 80)
                for category in categories:
                    print(f"\n{category}:")
                    print(f"说明：{descriptions.get(category, '无说明')}")
                
                return categories
            return []
                
        except Exception as e:
            print(f"生成分类失败: {str(e)}")
            print(f"生成分类失败: {result}")
            return []

    def run(self, mode='fetch_only', uncategorized_only=False):
        """
        运行完整的分类流程
        mode: 'fetch_only' 只获取仓库信息并保存到数据库
              'classify' 对数据库中的仓库进行分类和总结
              'getcategories' 使用AI生成合适的分类
        uncategorized_only: 是否只处理未分类的仓库
        """
        try:
            if mode == 'fetch_only':
                print("开始获取Starred仓库信息...")
                self.fetch_starred_repos()
                print("仓库信息已保存到数据库")
            elif mode == 'classify':
                print("开始对数据库中的仓库进行分类和总结...")
                self.classify_all_repos(uncategorized_only)
                print("分类和总结完成")
            elif mode == 'getcategories':
                print("开始分析仓库并生成合适的分类...")
                self.generate_categories()
                print("分类生成完成")
            else:
                print("无效的运行模式")
                return
        except Exception as e:
            print(f"运行失败: {str(e)}")
            raise

    def __del__(self):
        """清理资源"""
        self.fetch_executor.shutdown(wait=True)
        self.classify_executor.shutdown(wait=True) 