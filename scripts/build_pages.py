import os
import jinja2
from datetime import datetime
import glob

# 配置路径
MD_DIR = "./data"
OUTPUT_DIR = "./out"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# HTML模板（极简美观，适配论文列表）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>arXiv 论文日报</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { color: #3498db; margin-top: 30px; }
        .paper { margin: 15px 0; padding: 15px; border-radius: 5px; border: 1px solid #eee; }
        .meta { color: #666; font-size: 0.9em; margin: 5px 0; }
        .summary { line-height: 1.6; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>arXiv 论文日报 - {{ today }}</h1>
    <div class="meta">更新时间: {{ update_time }}</div>
    {{ content }}
</body>
</html>
"""

def read_markdown():
    """读取最新生成的markdown日报文件"""
    md_files = glob.glob(f"{MD_DIR}/digest_*.md")
    if not md_files:
        return "暂无论文数据"
    latest_md = sorted(md_files)[-1]
    with open(latest_md, "r", encoding="utf-8") as f:
        return f.read().replace("\n", "<br>")

def build_static_page():
    """生成静态HTML页面到out目录"""
    md_content = read_markdown()
    template = jinja2.Template(HTML_TEMPLATE)
    html_content = template.render(
        today=datetime.now().strftime("%Y-%m-%d"),
        update_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        content=md_content
    )
    with open(f"{OUTPUT_DIR}/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"静态网页生成完成：{OUTPUT_DIR}/index.html")

if __name__ == "__main__":
    build_static_page()
