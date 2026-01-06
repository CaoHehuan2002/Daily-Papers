import json
import os
from datetime import datetime
from pathlib import Path

# 解析项目根目录，确保无论从哪里运行都写入仓库内。
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "out"

# 读取markdown文件路径
today = datetime.now().strftime("%Y-%m-%d")
MD_PATH = DATA_DIR / f"digest_{today}.md"
# 输出目录（仓库根目录下的out）
os.makedirs(OUT_DIR, exist_ok=True)
HTML_PATH = OUT_DIR / "index.html"

def markdown_to_html(md_content):
    """简易的markdown转html（适配当前日报格式）"""
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>arXiv 论文日报 {today}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #3498db; margin-top: 30px; }}
        h3 {{ color: #2980b9; }}
        p {{ line-height: 1.6; color: #34495e; }}
        .topic-section {{ margin: 40px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
        .paper-item {{ margin: 20px 0; padding: 15px; border: 1px solid #e0e0e0; border-radius: 4px; }}
        .paper-title {{ font-size: 18px; font-weight: bold; color: #2980b9; }}
        .paper-meta {{ color: #7f8c8d; font-size: 14px; margin: 5px 0; }}
        .paper-summary {{ margin: 10px 0; line-height: 1.5; }}
    </style>
</head>
<body>
    <h1>arXiv 论文日报 - {today}</h1>
"""
    # 分割markdown内容，按主题处理
    lines = md_content.split("\n")
    in_topic = False
    in_paper = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 匹配主题标题（# 主题名）
        if line.startswith("# ") and not line.startswith("## "):
            # 切换主题之前关闭上一块，避免混乱的嵌套
            if in_paper:
                html += "        </div>\n"
                in_paper = False
            if in_topic:
                html += "    </div>\n"
            topic_name = line[2:]
            html += f'    <div class="topic-section">\n'
            html += f'        <h2>{topic_name}</h2>\n'
            in_topic = True
            in_paper = False
        # 匹配论文标题（## 1. [标题](链接)）
        elif line.startswith("## "):
            if in_paper:
                html += "        </div>\n"
            # 提取标题和链接
            title_part = line[3:]
            if "[" in title_part and "](" in title_part:
                title = title_part.split("[")[1].split("]")[0]
                link = title_part.split("](")[1].split(")")[0]
                html += f'        <div class="paper-item">\n'
                html += f'            <div class="paper-title"><a href="{link}" target="_blank">{title}</a></div>\n'
                in_paper = True
        # 匹配元信息（**arXiv ID**: xxx 等）
        elif line.startswith("**") and "**: " in line:
            key = line.split("**")[1]
            value = line.split("**: ")[1]
            html += f'            <div class="paper-meta"><strong>{key}:</strong> {value}</div>\n'
        # 匹配摘要内容
        elif line.startswith("**论文摘要**: "):
            summary = line.split("**论文摘要**: ")[1]
            html += f'            <div class="paper-summary"><strong>论文摘要:</strong> {summary}</div>\n'
        elif line.startswith("**核心总结**: "):
            summary = line.split("**核心总结**: ")[1]
            html += f'            <div class="paper-summary"><strong>核心总结:</strong> {summary}</div>\n'
    
    # 闭合标签
    if in_paper:
        html += "        </div>\n"
    if in_topic:
        html += "    </div>\n"
    html += """
</body>
</html>
"""
    return html

def build_html():
    """读取markdown文件，生成html页面"""
    if not os.path.exists(MD_PATH):
        print(f"未找到markdown文件：{MD_PATH}")
        # 生成空页面
        empty_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>arXiv 论文日报 {today}</title>
    <style>body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}</style>
</head>
<body>
    <h1>暂无论文数据</h1>
    <p>今日未抓取到符合条件的arXiv论文</p>
</body>
</html>
"""
        with open(HTML_PATH, "w", encoding="utf-8") as f:
            f.write(empty_html)
        print(f"生成空页面：{HTML_PATH}")
        return
    
    # 读取markdown内容
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # 转换为html
    html_content = markdown_to_html(md_content)
    
    # 保存html文件
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"静态页面生成完成：{HTML_PATH}")

if __name__ == "__main__":
    build_html()
