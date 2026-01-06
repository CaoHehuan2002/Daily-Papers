import yaml
import arxiv
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# 解析项目根目录，确保无论从哪里运行都写入仓库内。
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TOPICS_PATH = BASE_DIR / "topics.yml"

# 读取根目录的topics.yml配置文件
with open(TOPICS_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 创建data目录（自动生成）
os.makedirs(DATA_DIR, exist_ok=True)
# 汇总文件路径（保留所有论文）
ALL_OUTPUT_PATH = DATA_DIR / "arxiv_all.json"

def fetch_papers_by_topic():
    all_papers = []
    print(f"开始读取topics.yml的筛选规则，共 {len(config['profiles'])} 个主题")
    
    for profile in config['profiles']:
        topic_name = profile['name']
        include_keywords = profile.get('include', [])
        exclude_keywords = profile.get('exclude', [])
        categories = profile.get('categories', [])
        max_results = profile.get('max', 10)
        
        # 拼接arxiv的查询条件：分类 + 关键词
        query_terms = []
        if categories:
            query_terms += [f"cat:{cat}" for cat in categories]
        if include_keywords:
            query_terms += [f"title:{kw} OR abstract:{kw}" for kw in include_keywords]
        query = " AND ".join(query_terms) if query_terms else "*"

        # 调用arxiv接口爬取论文（最新提交优先）
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        topic_papers = []
        # 筛选论文：排除指定关键词
        for result in search.results():
            title_abs = f"{result.title} {result.summary}".lower()
            exclude_flag = False
            for ek in exclude_keywords:
                if ek.lower() in title_abs:
                    exclude_flag = True
                    break
            if exclude_flag:
                continue
            
            # 整理论文数据
            paper = {
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "arxiv_id": result.get_short_id(),
                "url": result.entry_id,
                "summary": result.summary.strip().replace("\n", " "),
                "published": result.published.strftime("%Y-%m-%d %H:%M"),
                "updated": result.updated.strftime("%Y-%m-%d %H:%M"),
                "category": topic_name,
                "categories": result.categories
            }
            topic_papers.append(paper)
            all_papers.append(paper)
        
        # 核心改动：为每个主题生成独立的json文件
        topic_json_name = f"arxiv_{topic_name.replace(' ','_')}.json"
        topic_json_path = DATA_DIR / topic_json_name
        with open(topic_json_path, "w", encoding="utf-8") as f:
            json.dump(topic_papers, f, ensure_ascii=False, indent=2)
        print(f"{topic_name} 主题爬取完成，共 {len(topic_papers)} 篇，保存至 {topic_json_name}")
    
    # 去重 + 按更新时间排序，保存汇总文件
    unique_papers = list({p['arxiv_id']: p for p in all_papers}.values())
    unique_papers.sort(key=lambda x: x['updated'], reverse=True)
    
    with open(ALL_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(unique_papers, f, ensure_ascii=False, indent=2)
    
    print(f"全部主题爬取完成！共获取 {len(unique_papers)} 篇论文，汇总保存至 arxiv_all.json")
    return unique_papers

if __name__ == "__main__":
    fetch_papers_by_topic()
