import os

def collect_code(root_dir, output_file, ignore_dirs=None, ignore_extensions=None):
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', 'node_modules', 'dist', 'venv', 'uploads', 'img', '.vscode'}
    if ignore_extensions is None:
        ignore_extensions = {
            '.pyc', '.pyo', '.exe', '.dll', '.so', '.png', '.jpg', '.jpeg', 
            '.gif', '.svg', '.ico', '.pdf', '.zip', '.tar', '.gz',
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.bin'
        }

    # 允许的文本文件扩展名（重点关注核心逻辑）
    allowed_extensions = {
        '.py', '.js', '.ts', '.vue', '.html', '.css', '.sh', '.bat', '.sql'
    }

    # 排除不重要的目录（如依赖、缓存、配置、文档、测试等）
    if ignore_dirs is None:
        ignore_dirs = {
            '.git', '__pycache__', 'node_modules', 'dist', 'venv', '.venv', 
            'uploads', 'img', '.vscode', 'doc', 'scripts', 'scratch', 
            'public', 'assets', 'site-packages', 'bin', 'lib', 'include', 'share'
        }

    # 进一步排除非核心逻辑的配置文件
    ignore_files = {
        'package-lock.json', 'yarn.lock', 'tsconfig.json', 'tsconfig.app.json', 
        'tsconfig.node.json', 'vite.config.ts', '.gitignore', 'README.md',
        'requirements.txt', 'seed_data.py', 'pydoc.bat', 'deactivate.bat', 
        'activate.bat', 'activate_this.py'
    }

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(root_dir):
            # 绝对路径拆分
            path_parts = root.split(os.sep)
            
            # 如果路径中包含任何需要忽略的目录名或者是虚拟环境/包目录，直接跳过并清空 dirs
            if any(d in path_parts for d in ignore_dirs) or '.venv' in path_parts or 'site-packages' in path_parts:
                dirs[:] = [] 
                continue
            
            # 过滤当前层级的目录列表 (避免进入)
            dirs[:] = [d for d in dirs if d not in ignore_dirs and d != '.venv' and d != 'site-packages']
            
            for file in files:
                if file in ignore_files or file == 'code.txt' or file == 'collect_all_code.py':
                    continue

                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                # 只处理允许的文本扩展名
                if ext not in allowed_extensions:
                    continue
                
                relative_path = os.path.relpath(file_path, root_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        outfile.write(f"\n{'='*80}\n")
                        outfile.write(f"FILE: {relative_path}\n")
                        outfile.write(f"{'='*80}\n\n")
                        outfile.write(content)
                        outfile.write("\n")
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")

if __name__ == "__main__":
    workspace_root = "/home/Yuhang/dev/TeamFlow"
    output_path = os.path.join(workspace_root, "code.txt")
    collect_code(workspace_root, output_path)
    print(f"Code collection complete. Saved to {output_path}")
