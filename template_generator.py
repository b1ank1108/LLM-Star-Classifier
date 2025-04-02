import os
import yaml
from db import Database, DatabaseError
from datetime import datetime

class TemplateGenerator:
    def __init__(self):
        try:
            # 加载配置
            with open('config.yaml', 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # 初始化数据库
            self.db = Database(self.config['database']['path'])
        except Exception as e:
            print(f"初始化失败: {str(e)}")
            raise

    def generate_readme(self, output_file='README.md'):
        """生成README文件"""
        try:
            # 获取所有仓库
            all_repos = self.db.get_all_repos()
            
            # 按分类组织仓库
            categorized_repos = {}
            for repo in all_repos:
                category = repo['category'] or '未分类'
                if category not in categorized_repos:
                    categorized_repos[category] = []
                categorized_repos[category].append(repo)
            
            # 生成分类统计
            category_stats = []
            for category, category_repos in categorized_repos.items():
                category_stats.append(f"- {category}: {len(category_repos)}个仓库")
            
            # 生成分类目录
            category_toc = []
            for category in sorted(categorized_repos.keys()):
                category_toc.append(f"- [{category}](#{category})")
            
            # 生成分类内容
            category_sections = []
            for category, category_repos in sorted(categorized_repos.items()):
                # 按名称排序仓库
                category_repos.sort(key=lambda x: x['name'].lower())
                
                # 生成该分类的仓库列表
                repo_list = []
                for repo in category_repos:
                    repo_list.append(f"- [{repo['name']}]({repo['url']}) - {repo.get('summary', repo['description'])}")
                
                # 添加分类标题和仓库列表
                category_sections.append(f"## {category}\n\n" + "\n".join(repo_list) + "\n")
            
            # 生成完整的README内容
            readme_content = f"""# GitHub Star 仓库分类

这是一个使用AI对GitHub Star的仓库进行分类和总结的工具。

## 统计信息

总仓库数：{len(all_repos)}个
分类数：{len(categorized_repos)}个

{chr(10).join(category_stats)}

## 目录

{chr(10).join(category_toc)}

## 分类详情

{chr(10).join(category_sections)}

## 贡献

欢迎提交Issue和Pull Request来帮助改进这个项目。

## 许可证

MIT License
"""
            
            # 写入README文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"README文件已生成: {output_file}")
            
        except Exception as e:
            print(f"生成README失败: {str(e)}")
            raise

    def _generate_repo_list(self, repos):
        """生成仓库列表"""
        return '\n'.join(
            f"""- [{repo['name']}]({repo['url']}) ![GitHub stars](https://img.shields.io/github/stars/{repo['name']}?style=flat-square) {repo['description'] or repo['ai_summary'] or '无描述'}"""
            for repo in sorted(repos, key=lambda x: x['name'])
        )

def main():
    generator = TemplateGenerator()
    generator.generate_readme()

if __name__ == "__main__":
    main() 