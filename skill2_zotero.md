# SKILL 2 · Zotero 去重 & 自动入库

## 职责
接收 SKILL 1 输出的文献列表，与本地 Zotero 库去重，然后通过 Zotero MCP 批量入库。

---

## 前置条件
- Zotero 本地客户端已运行
- Zotero MCP 已连接（通过 Better BibTeX 或 Zotero MCP Server）
- 目标 collection 名称已确认（不存在则自动创建）

---

## Step 1 · 去重检查

### 去重逻辑（按优先级）
```
1. DOI 精确匹配
   → 调用 zotero.search(doi=xxx)
   → 有结果 → 标记 status="exists"，跳过

2. 标题精确匹配（忽略大小写、标点）
   → 调用 zotero.search(title=xxx)
   → 相似度 ≥ 0.95 → 标记 status="exists"，跳过
   → 相似度 0.80~0.95 → 标记 status="possible_duplicate"，加入待确认列表

3. 其余 → 标记 status="new"，进入入库队列
```

### 去重后分组输出
```
new_items:              # 待入库，继续 Step 2
exists_items:           # 已存在，记录日志，不重复入库
possible_duplicates:    # 疑似重复，暂存，批量处理完后统一询问用户
not_found_items:        # SKILL 1 中标记 not_found 的，直接跳过
```

---

## Step 2 · 批量入库

### 每条文献的入库操作（按顺序执行）

```python
# 1. 创建文献条目
item_id = zotero.createItem({
    "itemType": detect_type(journal),  # journalArticle / conferencePaper / thesis
    "title": title,
    "creators": format_authors(authors),
    "date": str(year),
    "publicationTitle": journal,
    "DOI": doi,
    "abstractNote": abstract,
    "url": url,
    "extra": f"Citations: {citations}\nSource: {source}"
})

# 2. 自动下载 PDF（优先级顺序）
pdf_sources = [
    unpaywall(doi),          # 优先：开放获取
    semantic_scholar(doi),   # 次选
    arxiv(doi),              # 预印本
]
for src in pdf_sources:
    if src.available:
        zotero.attachPDF(item_id, src.url)
        break
else:
    # 所有来源均失败
    zotero.addNote(item_id, "PDF_PENDING: 请手动下载PDF")

# 3. 归入指定 collection
zotero.addToCollection(item_id, collection_name)

# 4. 自动打标签
zotero.addTags(item_id, [
    query_topic,             # 检索主题
    str(year)[:3] + "0s",   # 年代标签：如"2020s"
    source,                  # 来源："gs" / "cnki"
    "auto-imported"          # 标记为自动导入
])
```

### 批次控制
- 每批处理 **10 篇**，批次间等待 2 秒（避免 MCP 超时）
- 每批完成后输出进度报告（见下方格式）
- 记录 checkpoint：已完成的 item_id 列表，支持断点续传

---

## Step 3 · 入库日志

### 进度报告格式（每批10篇后输出）
```
📥 入库进度 [20/40]
✅ 成功入库: 18 篇
⏭️  跳过(已存在): 2 篇
📎 PDF已下载: 14 篇 | PDF待手动下载: 4 篇
```

### 最终汇总报告格式
```
═══════════════════════════════
📚 入库完成报告
═══════════════════════════════
✅ 新增入库:      38 篇
⏭️  跳过(已存在): 4 篇
⚠️  疑似重复:     2 篇（需确认）
❌ 未找到:        0 篇
📎 PDF下载成功:  31 篇
📝 PDF待处理:     7 篇

📁 Collection: "数字金融与不平等"
🏷️  标签已添加: 数字金融与收入不平等 / 2020s / auto-imported
═══════════════════════════════
```

---

## 疑似重复处理

批量任务完成后，如有 possible_duplicates，统一展示给用户：
```
⚠️ 发现 2 条疑似重复文献，请确认是否入库：

1. 新文献："Digital Finance and Rural Poverty" (Zhang, 2022)
   已有文献："数字金融与农村贫困" (张伟, 2022) [相似度: 88%]
   → [入库] [跳过]

2. ...
```

---

## 错误处理

| 情况 | 处理方式 |
|------|----------|
| Zotero MCP 连接断开 | 暂停任务，提示用户重启 Zotero，然后从 checkpoint 续传 |
| createItem 失败 | 记录错误，跳过该条，继续下一条 |
| collection 不存在 | 自动创建该 collection，继续入库 |
| PDF 所有来源均不可用 | 入库元数据，在备注中标记 PDF_PENDING |
