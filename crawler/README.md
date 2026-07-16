# 自行车设计资料采集器

当前版本每周一、周四自动运行，也可在 GitHub Actions 中手动运行。

采集原则：

- 第一阶段仅采集 Wikimedia Commons
- 只保留带开放授权或公有领域标记的图片
- 自动去重
- 所有新内容标记为“待审核”
- 不直接进入网站公开资料库

输出文件：

- `data/candidates.csv`：方便查看和导入表格
- `data/candidates.json`：供后续自动化程序使用

下一阶段将“待审核”数据写入 Google 表格的独立工作表。
