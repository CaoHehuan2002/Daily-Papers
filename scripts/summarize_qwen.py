import json
import os
import time
from datetime import datetime
import requests

# 读取爬取的论文数据
INPUT_PATH = "../data/arxiv.json"
OUTPUT_DIR = "../data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 获取当日日期（用于生成markdown文件名）
today = datetime.now().strftime("%Y-%m-%d")
OUTPUT_MD = f"{OUTPUT_DIR}/digest_{today}.md"

# 读取通义千问API_KEY
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

def load_papers():
    if not os.path.exists(INPUT_PATH):
        print("论文数据文件不存在！")
        return []
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_qwen_summary(text):
    """调用通义千问生成简洁摘要"""
    if not QWEN_API_KEY:
        return "未配置通义千问API_KEY，跳过摘要生成"
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {"role": "user", "content": f"请用简洁的中文总结这篇论文的核心创新点和研究内容，100字以内：{text}"}
            ]
        },
        "parameters": {"result_format": "text"}
    }
    try:
        res = requests.post(QWEN_API_URL, json=payload, headers=headers, timeout=15)
        res.raise_for_status()
        return res.json()["output"]["text"].strip()
    except Exception as e:
        return f"摘要生成失败: {str(e)[:50]}"

def generate_markdown(papers):
    """生成论文日报的markdown文件 - 按主题分组展示"""
    md_header = f"""# arXiv 论文日报 {today}
> 自动抓取并筛选 | 共 {len(papers)} 篇论文
---
"""
    md_body = ""

    # 核心改动：按主题分类整理论文
    topic_papers = {}
    for paper in papers:
        topic = paper["category"]
        if topic not in topic_papers:
            topic_papers[topic] = []
        topic_papers[topic].append(paper)

    # 遍历每个主题，分组写入markdown
    for topic_name, topic_paper_list in topic_papers.items():
        # 主题标题 + 分隔线
        md_body += f"""# {topic_name}
> 本组共 {len(topic_paper_list)} 篇论文
---
"""
        # 写入该主题下的所有论文
        for idx, paper in enumerate(topic_paper_list, 1):
            authors = ", ".join(paper["authors"])[:200]
            summary = paper["summary"][:500]
            qwen_summary = get_qwen_summary(summary)
            md_body += f"""## {idx}. [{paper['title']}]({paper['url']})
**arXiv ID**: {paper['arxiv_id']}
**作者**: {authors}
**更新时间**: {paper['updated']}
**论文摘要**: {summary}
**核心总结**: {qwen_summary}

---
"""

    # 拼接最终内容并保存
    md_content = md_header + md_body
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Markdown日报生成完成：{OUTPUT_MD}")

if __name__ == "__main__":
    papers = load_papers()
    if papers:
        generate_markdown(papers)
    else:
        print("无论文数据，跳过生成")
