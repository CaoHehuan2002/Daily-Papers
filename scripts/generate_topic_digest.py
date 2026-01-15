import os
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 配置项（可根据实际调整）
CONFIG = {
    "digest_file_pattern": r"^digest_(\d{4}-\d{2}-\d{2})\.md$",  # 匹配 digest_YYYY-MM-DD.md
    "gh_pages_branch": "gh-pages",
    "output_file_name": "digest.md"  # 每个topic文件夹下生成的文件名称
}

def execute_git_command(command, allow_fail=False, capture_output=False):
    """
    封装 Git 命令执行逻辑
    :param command: Git 命令字符串
    :param allow_fail: 是否允许命令执行失败（不抛出异常）
    :param capture_output: 是否捕获命令输出（返回结果）
    :return: 若 capture_output 为 True，返回命令输出结果
    """
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
    """
    查找并返回 gh-pages 分支下最新的 digest_YYYY-MM-DD.md 文件（仓库根目录）
    """
    # 切换到仓库根目录查找 digest 文件（避免在 scripts 目录下查找）
    repo_root_dir = Path(__file__).resolve().parent.parent
    digest_regex = re.compile(CONFIG["digest_file_pattern"])
    latest_file = None
    latest_date = None

    # 遍历仓库根目录下的所有文件
    for file in os.listdir(repo_root_dir):
        match = digest_regex.match(file)
        if match:
            # 解析文件中的日期字符串
            date_str = match.group(1)
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue  # 日期格式异常，跳过该文件

            # 对比找到最新的文件
            if (latest_date is None) or (file_date > latest_date):
                latest_date = file_date
                latest_file = repo_root_dir / file

    if not latest_file:
        raise Exception("未找到符合格式的 digest_YYYY-MM-DD.md 文件（仓库根目录）")
    
    return latest_file

def extract_topic_content(digest_content, topic_name):
    """
    从 digest 内容中提取指定 topic 对应的内容（匹配 ## topicName 到下一个 ## 之间的内容）
    :param digest_content: 完整的 digest 文件内容
    :param topic_name: 要提取的 topic 名称
    :return: 提取到的 topic 内容，无匹配时返回提示信息
    """
    # 构建正则表达式，匹配 ## 话题名 到下一个 ## 或文件末尾的所有内容
    regex_pattern = rf"## {re.escape(topic_name)}[\s\S]*?(?=## |$)"
    regex = re.compile(regex_pattern, re.IGNORECASE)
    match = regex.search(digest_content)

    if match:
        return match.group(0).strip()
    else:
        return f"未找到 {topic_name} 相关内容"

def main():
    try:
        # 1. 定义关键路径（核心修改：定位仓库根目录、根目录下的 topic.json）
        script_file = Path(__file__).resolve()
        scripts_dir = script_file.parent  # scripts 文件夹路径
        repo_root_dir = scripts_dir.parent  # 仓库根目录（scripts 文件夹的上级目录）
        topic_json_path = repo_root_dir / "topic.json"  # topic.json 位于仓库根目录

        # 2. 切换工作目录到仓库根目录（确保 Git 命令、文件操作基于仓库根目录）
        print(f"切换工作目录到仓库根目录：{repo_root_dir}")
        os.chdir(repo_root_dir)

        # 3. 切换到 gh-pages 分支并拉取最新代码
        print("切换并更新 gh-pages 分支...")
        # 检查 gh-pages 分支是否存在
        branch_exists = execute_git_command(
            f"git rev-parse --verify {CONFIG['gh_pages_branch']}",
            allow_fail=True,
            capture_output=True
        )
        
        if branch_exists:
            # 分支存在，切换并拉取最新代码
            execute_git_command(f"git checkout {CONFIG['gh_pages_branch']}")
            execute_git_command(f"git pull origin {CONFIG['gh_pages_branch']}")
        else:
            # 分支不存在，创建并切换
            execute_git_command(f"git checkout -b {CONFIG['gh_pages_branch']}")

        # 4. 读取并解析 topic.json（仓库根目录下）
        print("读取 topic.json...")
        if not topic_json_path.exists():
            raise Exception(f"topic.json 文件不存在：{topic_json_path}")
        
        with open(topic_json_path, "r", encoding="utf-8") as f:
            topics = json.load(f)
        
        if not isinstance(topics, list):
            raise Exception("topic.json 不是数组格式")
        
        # 提取有效 topic name（过滤空值）
        topic_names = [t.get("name") for t in topics if t.get("name")]
        if not topic_names:
            raise Exception("topic.json 中无有效 name 字段")

        # 5. 获取最新的 digest 文件并读取内容（仓库根目录下）
        print("查找最新的 digest 文件...")
        digest_file = get_latest_digest_file()
        print(f"读取 digest 文件：{digest_file}")
        
        with open(digest_file, "r", encoding="utf-8") as f:
            digest_content = f.read()

        # 6. 遍历 topic，创建文件夹并写入对应内容（仓库根目录下创建 topic 文件夹）
        print("开始生成/更新 topic 文件夹...")
        for topic_name in topic_names:
            # 创建 topic 文件夹（递归创建，已存在则忽略）
            topic_folder = repo_root_dir / topic_name
            topic_folder.mkdir(parents=True, exist_ok=True)
            if not topic_folder.exists():
                print(f"创建文件夹：{topic_folder}")

            # 提取该 topic 的内容并写入文件
            target_file = topic_folder / CONFIG["output_file_name"]
            topic_content = extract_topic_content(digest_content, topic_name)
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(topic_content)
            
            print(f"写入内容到：{target_file}")

        # 7. Git 提交并推送
        print("提交变更到 gh-pages 分支...")
        execute_git_command("git add .")

        # 构造提交信息
        current_date = datetime.now().strftime("%Y-%m-%d")
        commit_message = f"feat: 同步{current_date} digest内容到各topic文件夹"
        
        try:
            execute_git_command(f'git commit -m "{commit_message}"')
        except Exception as e:
            if "nothing to commit" in str(e):
                print("无内容变更，无需提交")
            else:
                raise e

        # 推送分支
        execute_git_command(f"git push origin {CONFIG['gh_pages_branch']}")
        print("操作完成！")

    except Exception as err:
        print(f"执行失败：{str(err)}")
        exit(1)

if __name__ == "__main__":
    main()
