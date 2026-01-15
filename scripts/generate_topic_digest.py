import os
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 配置项（可根据实际调整）
CONFIG = {
    "digest_file_pattern": r"^digest_(\d{4}-\d{2}-\d{2})\.md$",
    "gh_pages_branch": "gh-pages",
    "main_branch": "main",  # 新增：配置 main 分支名称（若为 master 可修改）
    "output_file_name": "digest.md"
}

def execute_git_command(command, allow_fail=False, capture_output=False):
    """封装 Git 命令执行逻辑（不变，复用原有函数）"""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8"
            )
            return result.stdout
        else:
            subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8"
            )
        print(f"Git 命令执行成功：{command}")
    except subprocess.CalledProcessError as e:
        if allow_fail:
            print(f"Git 命令执行失败（已允许）：{command}，错误信息：{e.stderr}")
            return None if not capture_output else e.stdout
        else:
            raise Exception(f"Git 命令执行失败：{command}，错误信息：{e.stderr}") from e

def get_latest_digest_file():
    """查找最新 digest 文件（不变，复用原有函数）"""
    repo_root_dir = Path(__file__).resolve().parent.parent
    digest_regex = re.compile(CONFIG["digest_file_pattern"])
    latest_file = None
    latest_date = None

    for file in os.listdir(repo_root_dir):
        match = digest_regex.match(file)
        if match:
            date_str = match.group(1)
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            if (latest_date is None) or (file_date > latest_date):
                latest_date = file_date
                latest_file = repo_root_dir / file

    if not latest_file:
        raise Exception("未找到符合格式的 digest_YYYY-MM-DD.md 文件（仓库根目录）")
    return latest_file

def extract_topic_content(digest_content, topic_name):
    """提取 topic 对应内容（不变，复用原有函数）"""
    regex_pattern = rf"## {re.escape(topic_name)}[\s\S]*?(?=## |$)"
    regex = re.compile(regex_pattern, re.IGNORECASE)
    match = regex.search(digest_content)

    if match:
        return match.group(0).strip()
    else:
        return f"未找到 {topic_name} 相关内容"

def main():
    try:
        # 1. 定位仓库根目录并切换工作目录（不变）
        repo_root_dir = Path(os.getenv("GITHUB_WORKSPACE", str(Path(__file__).resolve().parent.parent)))
        print(f"切换工作目录到仓库根目录：{repo_root_dir}")
        os.chdir(repo_root_dir)

        # 2. 先切换到 main 分支，读取 topic.json 并提取 topic_names（核心修改）
        print(f"切换到 {CONFIG['main_branch']} 分支，读取 topic.json...")
        execute_git_command(f"git checkout {CONFIG['main_branch']}")
        execute_git_command(f"git pull origin {CONFIG['main_branch']}")  # 拉取最新的 topic.json

        # 2.1 读取并解析 main 分支下的 topic.json
        topic_json_path = repo_root_dir / "topic.json"
        if not topic_json_path.exists():
            raise Exception(f"topic.json 文件不存在（{CONFIG['main_branch']} 分支）：{topic_json_path}")
        
        with open(topic_json_path, "r", encoding="utf-8") as f:
            topics = json.load(f)
        
        if not isinstance(topics, list):
            raise Exception("topic.json 不是数组格式")
        
        topic_names = [t.get("name") for t in topics if t.get("name")]
        if not topic_names:
            raise Exception("topic.json 中无有效 name 字段")
        print(f"从 {CONFIG['main_branch']} 分支成功读取 {len(topic_names)} 个有效 topic")

        # 3. 切换到 gh-pages 分支并拉取最新代码（原有逻辑，保留）
        print("切换并更新 gh-pages 分支...")
        branch_exists = execute_git_command(
            f"git rev-parse --verify {CONFIG['gh_pages_branch']}",
            allow_fail=True,
            capture_output=True
        )
        
        if branch_exists:
            execute_git_command(f"git checkout {CONFIG['gh_pages_branch']}")
            execute_git_command(f"git pull origin {CONFIG['gh_pages_branch']}")
        else:
            execute_git_command(f"git checkout -b {CONFIG['gh_pages_branch']}")

        # 4. 后续操作：使用内存中的 topic_names 执行 digest 处理（无需再读取 topic.json）
        print("查找最新的 digest 文件...")
        digest_file = get_latest_digest_file()
        print(f"读取 digest 文件：{digest_file}")
        
        with open(digest_file, "r", encoding="utf-8") as f:
            digest_content = f.read()

        print("开始生成/更新 topic 文件夹...")
        for topic_name in topic_names:  # 直接使用从 main 分支读取的 topic_names
            topic_folder = repo_root_dir / topic_name
            topic_folder.mkdir(parents=True, exist_ok=True)
            if not topic_folder.exists():
                print(f"创建文件夹：{topic_folder}")

            target_file = topic_folder / CONFIG["output_file_name"]
            topic_content = extract_topic_content(digest_content, topic_name)
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(topic_content)
            
            print(f"写入内容到：{target_file}")

        # 5. Git 提交并推送（原有逻辑，保留）
        print("提交变更到 gh-pages 分支...")
        execute_git_command("git add .")

        current_date = datetime.now().strftime("%Y-%m-%d")
        commit_message = f"feat: 同步{current_date} digest内容到各topic文件夹"
        
        try:
            execute_git_command(f'git commit -m "{commit_message}"')
        except Exception as e:
            if "nothing to commit" in str(e):
                print("无内容变更，无需提交")
            else:
                raise e

        execute_git_command(f"git push origin {CONFIG['gh_pages_branch']}")
        print("操作完成！")

    except Exception as err:
        print(f"执行失败：{str(err)}")
        exit(1)

if __name__ == "__main__":
    main()
