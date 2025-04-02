import argparse
from star_classifier import StarClassifier
from template_generator import TemplateGenerator

def main():
    parser = argparse.ArgumentParser(description='GitHub Star 仓库分类工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 获取仓库子命令
    fetch_parser = subparsers.add_parser('fetch', help='获取GitHub Star的仓库信息')
    
    # 分类子命令
    classify_parser = subparsers.add_parser('classify', help='对仓库进行分类')
    classify_parser.add_argument('-u', '--uncategorized-only',
                               action='store_true',
                               help='仅处理未分类的仓库')
    
    # 生成分类子命令
    categories_parser = subparsers.add_parser('gen-cat', help='使用AI生成合适的分类')
    
    # 生成文档子命令
    generate_parser = subparsers.add_parser('gen-readme', help='生成README文档')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    classifier = StarClassifier()
    
    if args.command == 'fetch':
        classifier.run('fetch_only')
    elif args.command == 'classify':
        classifier.run('classify', uncategorized_only=args.uncategorized_only)
    elif args.command == 'gen-cat':
        classifier.run('getcategories')
    elif args.command == 'gen-readme':
        generator = TemplateGenerator()
        generator.generate_readme('STAR.md')

if __name__ == "__main__":
    main() 