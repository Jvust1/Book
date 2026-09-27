# Book 学习系统 r2 开发增量

版本：1.0.0-rc6-dev / 20260927-learning-r2-dev。基于已核验的 rc5 源码，不是新的 Windows 可执行程序发布。

## 已实现

- 精讲主题 34 → 42，复习知识点 104 → 128，配套原创题 68 → 76，精讲映射目录 65 → 79。
- 新增主题：Hahn–Banach、一致有界原理、紧算子、广义导数、波动能量法、差分稳定性、货币政策工具、政府预算。
- 七本教材全部 845 个来源目录入口都有知识树节点，按章节、目录、知识类别和来源记录展开。719 个入口有可整理记录，其余为定位或习题索引等。树是来源整理，不是 845 节精讲完成。
- 10 道原书题接入题干、参考解答、方法总结：泛函分析第一章 6 道已有推导重组；公共财政第二、三章 4 道新编参考解答。原题及原推导文件未改。
- 考试工作台：期末速刷、建议重点、错题循环、章节测试。共 76 道配套题及 10 道方法化原题进入有解答队列。
- 章节测试计时、草稿保存、暂停续练、交卷后核对、自评及历史归档。暂停/关闭不停止计时；重新打开到期会话后交卷。应用离线关闭期间不会执行后台任务。
- 高频知识点目前显示“建议重点”，无历年真题频次依据，不声称必考。

## 来源边界

原始教材及学习状态的身份继续保留。知识树通过原有 chapter_id、显式章节编号或记录 ID 归属章节。不能确认的条目放在“目录归属待核对”，不按 PDF 页码猜测。当前该组条目数：当代中国经济 27、金融经济学 93、英文泛函分析 57；其中包含前后置页、索引及待补归属项，不能把这些数字等同于遗漏的正文章节数。

教学讲解、参考解答和方法总结都是附加层，未经过独立专家逐题审核。此版不是全书讲义完稿，不是全原书题解，也不是安全监考或自动评分系统。

## 验证与限制

- Node：45 项学习状态/考试选题测试通过；11 项生产渲染器及操作逻辑测试通过。
- Python：8 项覆盖、内容结构、来源引用和确定性检查通过。
- 全部 26,195 条记录、2,343 个来源页映射及 1,153 个图片条目的投影完整性检查通过。
- rc5 的 1,175 个原始来源、study 投影与图片文件逐字节哈希不变。
- 未运行本版 Go 构建、真实 Chromium/MathJax 布局和 Windows 实机验收。环境无 Go/Chromium；系统包安装受限，直接工具链下载不可达。Node VM 检查不替代真实浏览器验收。
- rc5 历史验证报告仍保留；本版只以 `verification/learning-r2-*` 与本说明为验证结论，不能沿用旧的 Windows 发布通过状态。

## 恢复与构建

先使用 GitHub `tools/restore_book_teaching_r1.py` 从冻结 rc4 源码及 rc5 增量恢复 rc5。然后用本包的 `apply_learning_delta.py`，提供 rc5 目录、本包 ZIP、GitHub 清单中的 SHA-256 和一个不存在的新目录。工具验证 rc5 的全部基线文件及全部恢复结果，不覆盖旧目录。

```sh
python apply_learning_delta.py --rc5-source /path/to/rc5 --delta Book-Learning-r2-Dev-Delta.zip --sha256 <trusted-manifest-sha256> --output /new/path/Book-Learning-r2
```

在恢复目录里：

```sh
python tools/build_teaching.py
python tools/build_learning.py
node --test tests/study_engine.test.cjs tests/teaching_engine.test.cjs tests/exam_engine.test.cjs tests/learning_ui_contract.test.cjs
python tests/learning_content_test.py
python tests/projection_integrity_test.py
python tools/pack_web.py
cd desktop
GOTOOLCHAIN=local GOPROXY=off go test ./...
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 GOTOOLCHAIN=local GOPROXY=off go build -trimpath -ldflags="-s -w -H windowsgui" -o ../Book-1.0.0-rc6-dev-Windows-x64.exe .
```

随后补跑既有 Chromium 回归与新增考试端到端验收，再做 Windows 实机验证；通过前保持开发版本。

## 交互参考

采用 Moodle 文档中的交卷后反馈原则、Anki 文档中的薄弱项筛选与复习队列原则，仅参考产品行为，未复制第三方源码或导入算法。
- https://docs.moodle.org/502/en/mod/quiz/mod
- https://docs.ankiweb.net/filtered-decks.html

## 下一批

优先补齐未有精讲的正文目录；逐题核对原书题干完整性并扩充方法化题解；补核金融经济学后段等目录归属。取得真实试卷后再增加可追溯的出现次数、年份和考试范围。
