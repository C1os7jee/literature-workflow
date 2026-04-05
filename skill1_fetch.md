# SKILL 1 · 文献抓取

## 职责
从 Google Scholar 和 CNKI 检索文献，返回结构化元数据列表。本模块只负责"找"，不负责入库。

---

## 模式 A · 主题搜索

### 输入
```
topic: string          # 研究主题，如"数字金融与收入不平等"
min_total: int         # 最少文献总数，默认 40
min_recent: int        # 近十年最少数量，默认 25
language: "zh"|"en"|"both"  # 检索语言，默认 both
```

### 检索策略

**第一轮：Google Scholar**
1. 构造主查询：`{topic}` 按引用数排序，时间不限，抓取前20条
2. 构造近十年查询：`{topic} after:{currentYear-10}` 抓取前20条
3. 扩展查询：提取主题的上位词/同义词，再检索一轮补充

**第二轮：CNKI 补充（当 language=zh 或 both）**
1. 在 CNKI 检索同主题中文文献
2. 优先来源：CSSCI、CSCD、北大核心
3. 补充10-15篇，避免与 GS 结果重复

**数量不足时的处理**
- 若结果 < min_total：自动放宽时间限制、拆解关键词重新检索
- 最多尝试3轮扩展，仍不足则返回已有结果并告知用户

### 排序规则
1. 引用数 > 100 的文献排最前
2. 同等引用数下，年份越新越靠前
3. 近十年文献与早期文献交替排列，保证覆盖度

### 输出格式（JSON）
```json
{
  "mode": "A",
  "query_topic": "数字金融与收入不平等",
  "search_timestamp": "2024-01-15T10:30:00",
  "total_found": 43,
  "recent_count": 27,
  "results": [
    {
      "id": 1,
      "title": "Digital Finance and Income Inequality",
      "authors": ["Zhang Wei", "Li Ming"],
      "year": 2023,
      "journal": "Journal of Finance",
      "doi": "10.1111/jofi.12345",
      "citations": 312,
      "abstract": "...",
      "source": "gs",
      "language": "en",
      "url": "https://...",
      "in_zotero": false
    }
  ]
}
```

---

## 模式 B · 精确查找

### 输入
```
items: list   # 文献列表，每条可以是以下任意格式：
              # - DOI: "10.1111/jofi.12345"
              # - 标题: "Digital Finance and Income Inequality"
              # - APA格式引用: "Zhang, W. (2023). Digital..."
              # - 混合列表均可
```

### 处理逻辑
1. 解析每条输入，识别格式类型
2. DOI → 直接调用 CrossRef API 获取元数据
3. 标题 → Google Scholar 精确搜索，取相似度最高的结果
4. APA 引用 → 提取作者+年份+标题，再精确搜索
5. 每条返回置信度评分（0-1），低于 0.8 时标记为"需人工确认"

### 输出格式（JSON）
```json
{
  "mode": "B",
  "total_input": 15,
  "resolved": 13,
  "needs_review": 2,
  "results": [
    {
      "id": 1,
      "input_raw": "10.1111/jofi.12345",
      "input_type": "doi",
      "confidence": 1.0,
      "title": "...",
      "authors": [...],
      "year": 2023,
      "journal": "...",
      "doi": "10.1111/jofi.12345",
      "abstract": "...",
      "url": "https://...",
      "in_zotero": false,
      "flag": null
    },
    {
      "id": 2,
      "input_raw": "某篇模糊标题",
      "input_type": "title",
      "confidence": 0.71,
      "flag": "needs_review",
      "candidates": [...]
    }
  ]
}
```

---

## 错误处理

| 情况 | 处理方式 |
|------|----------|
| GS 访问受限/超时 | 等待5秒重试，最多3次，仍失败则跳过并记录 |
| DOI 在 CrossRef 查不到 | 降级到 GS 标题搜索 |
| 文献无摘要 | abstract 字段填 "N/A"，不影响入库 |
| 找不到任何匹配 | 标记 flag="not_found"，跳过入库 |
