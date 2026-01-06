# 测试说明

这个目录用于放置 arXiv 日报流水线相关的自动化测试。

建议覆盖：
- 纯函数的单元测试（如 markdown 解析 / HTML 生成）。
- 流水线的集成测试（抓取 -> 摘要 -> 构建），并对网络/API 调用做 mock。

运行方式（添加 pytest 等测试框架后）：
```
python -m pytest
```

注意事项：
- 不要在测试中发起真实网络请求；mock `requests.post` 和 `arxiv.Search`。
- 保持测试可重复、可预测；尽量使用固定日期/固定数据。
