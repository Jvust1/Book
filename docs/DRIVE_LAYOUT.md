# Book Google Drive 目录约定

Google Drive 项目根目录：`Book`

当前结构：

```text
Book/
├── 00_Project/
├── 01_Textbooks/
├── 02_Lectures/
├── 03_Exports/
└── 04_Backups/
```

## 00_Project

保存非代码项目资料，例如：

- 产品需求记录
- 设计截图
- 课程配置说明
- 人工确认记录
- 测试报告
- 阶段验收材料

GitHub 中的 Markdown 文档仍是产品 / 架构规范的主版本；Drive 主要存放大型二进制文件和使用材料。

## 01_Textbooks

保存教材相关原始资产。

建议后续按课程再分：

```text
01_Textbooks/
└── <CourseName>/
    ├── Incoming/
    ├── Main/
    ├── Supplementary/
    ├── English/
    ├── Reference/
    └── Versions/
```

其中：

- `Incoming`：刚上传、尚未确认身份的教材
- `Main`：主教材
- `Supplementary`：辅助教材
- `English`：英文教材
- `Reference`：参考教材
- `Versions`：同一本教材的历史版本 / 更新版本

原始 PDF 不应因为结构化完成而删除。

## 02_Lectures

保存课堂原始录音和必要的大型课堂资产。

建议后续按课程：

```text
02_Lectures/
└── <CourseName>/
    ├── Audio/
    ├── Attachments/
    └── Imported/
```

结构化后的字幕、课堂事件、时间戳关系应进入应用数据库；Drive 中主要保留原始音频和大型附件。

## 03_Exports

保存从系统导出的结果，例如：

- 结构化教材导出包
- JSON / JSONL
- 题库导出
- 考点报告
- 章节总结导出
- 数据迁移包
- 测试样例

## 04_Backups

保存阶段性备份，例如：

- 结构化数据库快照
- 发布前数据备份
- 教材映射表备份
- 迁移前备份

## GitHub 与 Drive 的职责分工

### GitHub

主要保存：

- 源代码
- Schema
- API 定义
- 产品规范
- 数据模型
- 交互规范
- Roadmap
- 自动化脚本
- 测试代码

### Google Drive

主要保存：

- 原始教材 PDF
- 教材大图 / 大型资源
- 课堂录音
- 用户提供的大型附件
- 导出包
- 阶段备份

## 文件身份约定

应用数据库不应只通过 Drive 文件名识别教材。

每个导入文件至少记录：

```text
source_provider = google_drive
source_file_id
source_file_name
file_hash
course_id
book_id
book_version_id
imported_at
```

文件被重命名或移动后，仍尽量通过稳定文件 ID 和哈希识别。

## 安全约束

- 不把大型教材 PDF 直接提交到 GitHub 仓库。
- 不把课堂原始录音提交到 GitHub。
- 不因新版本教材上传而覆盖旧版本原文件。
- 删除 Drive 原始教材前必须确认应用已有可靠备份与映射。
