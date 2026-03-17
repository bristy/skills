---
name: thu-thesis
description: 清华大学毕业论文 Word → PDF 一键格式规范化工具。输入任意 Word (.docx) 格式的清华毕业论文，自动转换为符合清华 thuthesis 官方 LaTeX 模板规范的高质量 PDF。适用于所有清华学位论文（MBA/学硕/专硕），一条命令搞定。功能：自动提取章节结构、中英文摘要、参考文献（自动生成 BibTeX）、图片（含 caption）、表格（含表头和标题）、致谢、个人简历；自动生成符号和缩略语说明（含孤儿缩略语检测与正文首次出现处自动补写）；自动生成插图清单和附表清单；输出完整 thuthesis LaTeX 项目并编译为 PDF。运行时依赖：python-docx、jinja2、xelatex/bibtex（TeX Live）；setup.sh 会从 GitHub 克隆 thuthesis 到 /tmp/thuthesis-latest。Use when: 用户需要把 Word 格式的清华毕业论文转为规范 PDF，或需要对毕业论文做格式规范化处理。
---

# 清华 MBA 论文 Word → PDF 一键转换

## ⚠️ 核心操作原则（不得违反）

> **只从 Word 中提取信息，不修改 thuthesis 模板格式。**
>
> - thuthesis 的封面、页眉、目录、参考文献、图表样式等，全部由 `thuthesis.cls` 自动生成
> - 脚本只负责把 Word 里的内容（标题、摘要、章节、图表、参考文献等）提取出来填入 `.tex` 文件
> - 若 Word 中某字段缺失，对应 LaTeX 字段留空，**不删除**、不跳过、不用占位符替代
> - 任何格式上的"改进"都必须以 `assets/databk/` 中的官方示例为准，不得自行发挥

## 架构：新三层 AI-native 流程

```
Word 文件
  ↓ [extract_raw.py]  纯机械提取，无 LLM
raw_xxx.json + 文档骨架（段落 idx + 样式 + 文字）
  ↓ [我（AI）阅读骨架]  理解章节结构
struct_xxx.json（章节划分、段落 idx 映射）
  ↓ [build_parsed.py]  纯 Python 组装，无 LLM
parsed_xxx.json
  ↓ [render.py]        填充 thuthesis LaTeX 模板
LaTeX 项目目录
  ↓ [xelatex + bibtex] 编译
thesis.pdf ✅
  ↓ [evaluate.py]      Rubric 评测
evaluation_report.md
```

**关键设计原则：Python 脚本不调用任何 LLM，不持有 API key。AI 只在中间的"阅读理解"步骤介入，通过工具调用或直接输出 struct.json 完成。**

## 依赖

```bash
pip3 install python-docx jinja2 matplotlib
# 需要已安装 TeX Live
```

## 格式参考：assets/databk/

`assets/databk/` 是从官方 thuthesis 项目备份的原始示例 data 文件，是本工具一切格式决策的**黄金标准**：

| 文件 | 参考内容 |
|------|----------|
| `chap01.tex` ~ `chap04.tex` | 正文章节、三线表、图片、公式格式 |
| `abstract.tex` | 中英文摘要格式 |
| `denotation.tex` | 缩略语/符号说明格式 |
| `acknowledgements.tex` | 致谢格式 |
| `resume.tex` | 个人简历格式 |

**遇到任何格式问题，先查 `databk/` 里的对应文件，再动代码。**

## 初次使用：拉取 thuthesis 格式参考

```bash
SKILL_DIR="${WORKSPACE}/skills/thu-thesis"
bash "$SKILL_DIR/scripts/setup.sh" "$SKILL_DIR"
```

## 完整转换流程

### Step 1：机械提取

```bash
SKILL_DIR="${WORKSPACE}/skills/thu-thesis"
python3 "$SKILL_DIR/scripts/convert.py" extract <论文.docx> [output_dir]
```

输出：
- `output/raw_xxx.json`：段落、表格、图片的机械提取结果
- 终端打印文档骨架（`idx [样式] 文字`），供 AI 阅读

### Step 2：AI 阅读骨架，生成 struct.json

AI（我）读取骨架，识别：
- 摘要范围（`abstract_cn_range`, `abstract_en_range`）
- 各章节标题段落 idx（`title_para`）、正文范围（`content_range`）
- 各级小节（sections）的 idx 和编号
- 参考文献、致谢、简历的范围

输出 `struct_xxx.json`，格式：

```json
{
  "cover": {
    "abstract_cn_range": [27, 31],
    "abstract_en_range": [35, 44],
    "keywords_cn_para": 31,
    "keywords_en_para": 44
  },
  "chapters": [
    {
      "number": "第1章",
      "title": "引言",
      "title_para": 109,
      "content_range": [110, 142],
      "sections": [
        {"level": 2, "number": "1.1", "title": "选题背景", "title_para": 110},
        {"level": 3, "number": "1.1.1", "title": "子节标题", "title_para": 115}
      ]
    }
  ],
  "references_range": [388, 409],
  "acknowledgements_range": [412, 412],
  "resume_range": [423, 428]
}
```

### Step 3-6：组装、渲染、编译、评测

```bash
python3 "$SKILL_DIR/scripts/convert.py" build \
  output/raw_xxx.json \
  struct_xxx.json \
  ./output-latex-dir
```

自动完成：
- `build_parsed.py`：raw + struct → parsed JSON（含表格、图片正确插入）
- `render.py`：parsed JSON → LaTeX 项目
- `xelatex + bibtex`：编译 PDF
- `evaluate.py`：Rubric 评测

## 文件说明

| 路径 | 说明 |
|------|------|
| `scripts/convert.py` | 入口，`extract` / `build` 两个子命令 |
| `scripts/extract_raw.py` | Word → raw JSON（纯机械提取，段落/表格/图表） |
| `scripts/build_parsed.py` | raw + struct → parsed JSON（纯 Python，无 LLM） |
| `scripts/render.py` | parsed JSON → LaTeX 项目（填充模板，生成 BibTeX） |
| `scripts/evaluate.py` | Rubric 评测，输出 evaluation_report.md |
| `scripts/llm_parse.py` | ⚠️ 已废弃，仅作备用参考 |
| `scripts/parse_docx.py` | ⚠️ 已废弃，仅作备用参考 |
| `assets/templates/*.j2` | Jinja2 模板 |
| `assets/databk/` | **thuthesis 官方格式示例，格式决策唯一参考** |

## Step 5：评测后自动修复（不询问用户）

**评测结果出来后，立即判断哪些问题可以工具修复，直接修复，无需等待确认。**

### 可自动修复的问题

| 问题 | 修复方式 |
|------|---------|
| BibTeX author/title 字段为空 | 修 render.py 解析逻辑 → 重跑 render + compile |
| C7 author-year 引用未转 \cite | 修正则 → 重跑 render + compile |
| LaTeX 编译报错（\& 转义等） | 修 render.py 转义逻辑 → 重跑 compile |

### 不可自动修复的问题

| 问题 | 原因 |
|------|------|
| 表格/图片无 caption | Word 原文没有，工具无中生有 |
| C5 文献未被正文引用 | Word 正文本来就没引用，已用 \nocite 兜底 |
| C7 author-year 匹配失败 | 姓名简称无法映射，原文限制 |
| committee/comments/resolution 占位 | 答辩后才有内容 |

修复循环最多 **3 次**，防止无限循环。

## Rubric 评测（evaluate.py）

```bash
python3 "$SKILL_DIR/scripts/evaluate.py" <parsed.json> <latex_dir>
```

### 评分制度

- **必要项（满分3分）**：PASS=3，WARN=1.5，FAIL=0
- **重要项（满分2分）**：PASS=2，WARN=1，FAIL=0
- **亮点项（满分1分）**：PASS=1，WARN=0.5，FAIL=0
- **失误扣分项（满分0）**：错误1处扣1分，最多扣10分
- 最终：总分/满分（百分比）+ 优秀≥90% / 良好≥75% / 合格≥60%

### 报告要求

**所有扣分项必须写明原因**，明细表说明列**不截断**。

### 评测维度（35项）

| 维度 | 检查内容 |
|------|----------|
| A. 元信息 | 中英文标题、作者、导师、院系、日期、摘要、关键词 |
| B. 正文 | 章节结构、.tex文件、文字总量、节级标题、**目录结构一致性（B5）** |
| C. 参考文献 | 列表完整、BibTeX、字段、条目数、引用覆盖率、关联性、author-year |
| D. 图片 | 提取数量、caption、LaTeX渲染 |
| E. 表格 | 提取数量、三线表格式、caption |
| F. 缩略语 | 缩略语表、孤儿缩略语 |
| G. 附件 | 致谢、简历 |
| H. 编译 | PDF已生成、无Error、thusetup格式 |

## 参考文献处理

- Word 原文参考文献列表 → `ref/refs.bib`（自动解析为 BibTeX）
- 正文 `[10]` → `\cite{key}`，支持 `[1,2,3]` 和 `[1-3]`
- **Author-year 行文引用自动补 `\cite`**：
  - `曹玉（2025）分析了...` → `曹玉（2025）\cite{cao2025aigc}分析了...`
  - 支持中文全角 `（年）`、英文半角 `(年)`
  - 匹配失败时保留原文，rubric C7 会警告
- 未被引用文献：关键词匹配补 `\cite`；无匹配用 `\nocite` 兜底

## 表格格式（三线表）

```latex
\begin{table}[htbp]
  \centering
  \caption{表题}
  \begin{tabularx}{\textwidth}{lX}
    \toprule
    短列头 & 长文本列头 \\
    \midrule
    内容1 & 内容2 \\
    \bottomrule
  \end{tabularx}
\end{table}
```
- 无竖线，三线（toprule/midrule/bottomrule）
- 短列（≤12字符宽）用 `l`，长文本列用 `X`；至少一个 `X`
- caption 在表格上方

## 图表提取（extract_raw.py）

- 普通图片：从 docx 关系表提取 `a:blip` 引用，保存到 `output/figures/`
- 图表对象（`c:chart`）：解析 XML 数据，用 matplotlib 渲染为 PNG
- SVG 跳过（LaTeX 不直接支持）
- caption 检测：图片后 0-2 段内匹配 `^图\s*\d` 模式

## 已知限制

- SVG 图片跳过
- committee.tex / comments.tex / resolution.tex 为占位，需手工填写
- `.doc` 格式需先转 docx

## thuthesis 配置（MBA 专业硕士）

```latex
\thusetup{
  degree = {master},
  degree-type = {professional},
  degree-category = {工商管理硕士},
  degree-category* = {Master of Business Administration},
  department = {经济管理学院},
}
```
