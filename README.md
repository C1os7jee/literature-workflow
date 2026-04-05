# literature-workflow

`literature-workflow` 是一个文献工作流技能集合，用来把“检索文献、核对题录、导入 Zotero、去重复用、生成阅读笔记”串成一条更稳定的流程。

这个项目的定位不是单一检索脚本，而是一个顶层编排技能：

- 中文文献优先走 CNKI 工作流
- 英文与国际文献优先走 Google Scholar 工作流
- 入库、去重、复用、笔记写回优先走 Zotero MCP
- 顶层技能负责按任务类型选择模式、路由工具、汇总结果

## 适用场景

- 给定研究主题，检索并筛选中英文文献
- 给定 DOI、题名列表或参考文献列表，解析并校正文献信息
- 检查文献是否已经在 Zotero 中存在，避免重复入库
- 将确认后的文献导入 Zotero 指定集合
- 为已确认文献生成结构化阅读笔记或综述素材

## 工作模式

项目内置两种主模式：

- Mode A: 主题检索、文献筛选、可选的阅读整理
- Mode B: DOI、标题、参考文献列表解析与 Zotero 入库

顶层入口是 [SKILL.md](SKILL.md)，分发逻辑主要写在 [skill3_batch.md](skill3_batch.md)。

## 目录结构

- [SKILL.md](SKILL.md)
  顶层技能说明，负责整体路由与规则约束。
- [skill1_fetch.md](skill1_fetch.md)
  检索、验证、题录解析相关流程。
- [skill2_zotero.md](skill2_zotero.md)
  Zotero 去重、复用、导入与回退策略。
- [skill3_batch.md](skill3_batch.md)
  批处理分发器与执行策略。
- [skill4_review.md](skill4_review.md)
  阅读笔记、结构化整理与输出规范。
- [cnki-skills](cnki-skills)
  面向 CNKI 的检索、详情提取、期刊检索、导出等子技能。
- [gs-skills](gs-skills)
  面向 Google Scholar 的检索、被引追踪、全文链接、导出等子技能。
- [zotero-mcp](zotero-mcp)
  与 Zotero 交互的 MCP 侧能力与测试代码。
- [references](references)
  触发提示词与辅助说明。
- [agents](agents)
  代理配置文件。

## 使用思路

推荐先由顶层技能判断任务类型，再按需加载子模块，而不是一开始把所有子技能全部读入。

常见路由方式：

- 中文题名、中文期刊、核心期刊判断、中文学位论文：优先 CNKI
- 英文题名、DOI 校验、被引扩展、国际文献发现：优先 Google Scholar
- Zotero 查重、集合管理、笔记写入、元数据修正：优先 Zotero MCP

## 参考与致谢

本项目参考并整合了以下仓库的思路与部分结构：

- [cookjohn/gs-skills](https://github.com/cookjohn/gs-skills)
- [cookjohn/cnki-skills](https://github.com/cookjohn/cnki-skills)
- [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp)

如果你准备把这个仓库继续公开维护，建议后续在提交说明或仓库说明中持续保留这些来源信息。
