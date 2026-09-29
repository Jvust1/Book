# Drive 大文件上传失败处理规则

适用范围：Book 项目以及同类长期项目中的大文件交付。

## 固定规则

当单个文件因为 Google Drive / 连接器大小限制或上传稳定性问题无法直接上传时：

1. **不要降低内容质量，不要重新压缩或删内容来规避限制。**
2. 保留原文件不变，记录原文件：
   - 文件名
   - 字节大小
   - SHA-256
3. 按**原始字节**拆成多个连续分卷，例如：
   - `.part00`
   - `.part01`
   - `.part02`
4. 每个分卷分别记录：
   - 文件名
   - 字节大小
   - SHA-256
5. 上传到 Drive：
   - 全部分卷
   - 分卷 manifest
   - 恢复说明
   - **Colab 合并 Notebook**
6. Notebook 必须能够：
   - 挂载 Google Drive
   - 自动按编号排序分卷
   - 流式合并，避免占满 RAM
   - 输出完整文件 SHA-256
   - 可选核对 EXPECTED_SHA256
   - 若输出为 ZIP，执行 ZIP 完整性测试
7. 每次使用此方案时，**必须把 Notebook 的 Google Drive 链接直接发给用户**，不能只给本地 sandbox 链接。
8. Drive 中的通用 Notebook：
   - 文件：`Drive_大文件分卷合并工具.ipynb`
   - Drive ID：`1Pf_fGDwoG814gOl-FjIJ-bnFAAp2AVTy`
   - 位置：`Book/00_Project/Colab_Tools/`
9. 分卷上传完成后，应在项目 checkpoint / receipt 中记录：
   - 原文件 SHA-256
   - 分卷列表及 SHA-256
   - Notebook Drive ID / 链接
   - 恢复方式
10. 若未来上传接口允许完整文件稳定上传，可额外上传完整文件；但不得删除已发布的可验证分卷，除非明确整理历史版本。

## 原则

**大文件上传失败时，优先“原字节分卷 + Colab 无损合并 + 哈希校验”，而不是牺牲内容或文件质量。**
