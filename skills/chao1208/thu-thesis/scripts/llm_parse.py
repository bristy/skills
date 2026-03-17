"""
llm_parse.py - 用 LLM 理解论文结构，Python 负责内容填充

两步走：
  Step 1: 发"骨架"给 LLM（只含短文本/标题类段落）→ 得到结构标注
  Step 2: Python 按 idx 范围把正文内容填回去

用法：
  ANTHROPIC_API_KEY=xxx ANTHROPIC_BASE_URL=https://... python3 llm_parse.py raw_xxx.json [out_dir]
"""

import json, os, re, sys, subprocess, tempfile
from pathlib import Path

# ─── Step1 prompt：只让 LLM 做结构识别 ───────────────────────────────────────

SYSTEM = """你是论文结构解析助手。给你一份段落索引表，每行格式：
[编号] [样式] | 文本（最多40字）

任务：识别每个段落属于哪个区域，输出结构标注。
不需要输出正文内容，只输出结构骨架。

重要规则：
1. 样式为 toc/toc1/toc2/toc3 的段落是目录页，直接忽略
2. 封面信息（作者、导师等）通常在论文开头，带"作者："、"指导教师："等标签
3. 摘要以"摘要"或"Abstract"标题段开始
4. 正文章节以"第N章"格式的标题开始（Heading 1 或 Title1 样式）
5. 参考文献以"参考文献"标题段开始，之后每段是一条文献
6. 保留章节的原始编号（第1章就是第1章，第3章就是第3章）"""

USER_TMPL = """论文段落（共{n}段，正文已截短）：
{skeleton}

请输出以下JSON（严格格式，不要额外说明）：
{{
  "meta_paras": [段落编号列表，封面信息所在段落],
  "abstract_cn_range": [起始编号, 结束编号],
  "keywords_cn_para": 段落编号或null,
  "abstract_en_range": [起始编号, 结束编号],
  "keywords_en_para": 段落编号或null,
  "chapters": [
    {{
      "title_para": 段落编号,
      "number": "第3章",
      "title": "章节标题（不含章号）",
      "sections": [
        {{"title_para": 编号, "level": 2, "number": "3.1", "title": "节标题"}},
        {{"title_para": 编号, "level": 3, "number": "3.1.1", "title": "小节标题"}}
      ],
      "content_range": [起始编号, 结束编号]
    }}
  ],
  "references_range": [起始编号, 结束编号],
  "acknowledgements_range": [起始编号, 结束编号或null],
  "resume_range": [起始编号或null, 结束编号或null],
  "statement_range": [起始编号或null, 结束编号或null]
}}"""


def build_skeleton(paragraphs, max_lines=300):
    """只发结构相关段落给 LLM：跳过 toc，截断正文，保留标题和封面"""
    TITLE_STYLES = {'Heading 1','Heading 2','Heading 3','Heading 4',
                    'Title','Title1','heading 1','heading 2','heading 3',
                    '标题1','标题2','标题3','Heading1','Heading2','Heading3'}
    TOC_STYLES = {'toc 1','toc 2','toc 3','toc 4','toc1','toc2','toc3','toc4',
                  'table of figures','TOC 1','TOC 2','TOC 3'}
    lines = []
    for p in paragraphs:
        text = p.get('text','').strip()
        if not text:
            continue
        style = p.get('style','')
        idx = p.get('idx',0)
        # 跳过目录段落
        if style in TOC_STYLES or style.lower().startswith('toc'):
            continue
        # 标题类保留全文；正文截到40字
        if style not in TITLE_STYLES and len(text) > 40:
            text = text[:40] + '…'
        lines.append(f"[{idx:04d}] [{style}] | {text}")
        if len(lines) >= max_lines:
            lines.append(f"…(仅显示前{max_lines}段，共{len(paragraphs)}段)")
            break
    return '\n'.join(lines)


def call_llm(system, user, api_key, base_url, model="claude-sonnet-4-6"):
    """用 curl streaming 调用，返回完整文本"""
    payload = {"model": model, "max_tokens": 4000, "stream": True,
               "system": system, "messages": [{"role": "user", "content": user}]}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
        pfile = f.name

    url = base_url.rstrip('/') + '/v1/messages'
    cmd = ['curl', '-s', '--max-time', '120', '-N',
           '-H', f'x-api-key: {api_key}',
           '-H', 'anthropic-version: 2023-06-01',
           '-H', 'content-type: application/json',
           '-d', f'@{pfile}', url]

    chunks = []
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in proc.stdout:
        line = line.strip()
        if line.startswith('data: '):
            s = line[6:]
            if s == '[DONE]': break
            try:
                d = json.loads(s)
                if d.get('type') == 'content_block_delta':
                    t = d.get('delta',{}).get('text','')
                    if t: chunks.append(t)
            except: pass
    proc.wait()
    os.unlink(pfile)
    return ''.join(chunks)


def paras_in_range(paragraphs, start_idx, end_idx):
    """取 idx 在 [start, end] 范围内的段落文本"""
    return [p for p in paragraphs if start_idx <= p.get('idx',0) <= end_idx]


def paras_text(paragraphs, start_idx, end_idx):
    return '\n'.join(p['text'] for p in paras_in_range(paragraphs, start_idx, end_idx)
                     if p.get('text','').strip())


def extract_meta_from_tables(tables):
    """从封面表格提取 meta 字段"""
    meta = {k: '' for k in ['title','title_en','author','author_en',
                              'supervisor','supervisor_en','department',
                              'degree_category','degree_category_en',
                              'discipline','discipline_en','date']}
    BLACKLIST = re.compile(r'评阅|答辩|委员会|授权|声明|使用授权|学位论文公开|保密|版权|清华大学')

    for t in tables[:5]:  # 封面表格通常在前几个
        rows = t.get('rows', [])
        # 扁平化所有单元格文本
        cells = []
        for row in rows:
            for cell in row:
                text = str(cell).strip()
                if text:
                    cells.append(text)

        for i, cell in enumerate(cells):
            # 标题：最长中文非黑名单单元格
            if (re.search(r'[\u4e00-\u9fff]', cell) and len(cell) > 5
                    and not BLACKLIST.search(cell) and not meta['title']
                    and '申请清华大学' not in cell):
                meta['title'] = cell
            # 英文标题
            if (re.match(r'^[A-Z]', cell) and len(cell) > 15
                    and not re.search(r'[\u4e00-\u9fff]', cell)
                    and 'University' not in cell and not meta['title_en']):
                meta['title_en'] = cell
            # 作者（中文）— 兼容"申  请  人"全角空格形式
            if re.sub(r'\s', '', cell) in ('申请人', '作者') and i+2 < len(cells):
                meta['author'] = cells[i+2].strip()
            # 英文作者（by xxx 格式）
            m = re.search(r'^by\s+([A-Z][A-Za-z\s]+)$', cell)
            if m:
                meta['author_en'] = m.group(1).strip()
            # 导师 — 兼容全角空格
            if re.sub(r'\s', '', cell) in ('指导教师', '导师') and i+2 < len(cells):
                meta['supervisor'] = cells[i+2].strip()
            # 院系 — 兼容全角空格
            if re.sub(r'\s', '', cell) in ('培养单位', '院系', '学院') and i+2 < len(cells):
                meta['department'] = cells[i+2].strip()
            # 学位类型
            if cell in ('学位类别', '申请学位') and i+2 < len(cells):
                meta['degree_category'] = cells[i+2].strip()
            # 日期 — 支持阿拉伯数字和中文数字格式（如"二○二六年五月"）
            CN_DIGITS = {'○':'0','一':'1','二':'2','三':'3','四':'4',
                         '五':'5','六':'6','七':'7','八':'8','九':'9'}
            def cn_to_arabic(s):
                return ''.join(CN_DIGITS.get(c, c) for c in s)
            cell_arabic = cn_to_arabic(cell)
            m = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月', cell_arabic)
            if m and not meta['date']:
                meta['date'] = f"{m.group(1)}-{int(m.group(2)):02d}"

    return meta


def build_chapter_content(chap_struct, paragraphs, next_chap_start, figures_by_para=None, tables_by_para=None):
    """把章节内容段落组装成 content 列表，含图片块和表格块"""
    content = []
    cr = chap_struct.get('content_range', [0, 9999])
    start, end = cr[0], cr[1] if cr[1] else next_chap_start - 1

    # 收集本章所有 section 标题的 para_idx，用于插入 section 块
    sec_map = {}
    for sec in chap_struct.get('sections', []):
        sec_map[sec['title_para']] = sec

    # figures_by_para: {para_idx: [figure_info, ...]}
    fig_map = figures_by_para or {}
    # tables_by_para: {before_para_idx: [table_info, ...]}
    tbl_map = tables_by_para or {}

    # 找图题：图片后面紧接的"图X-X ..."段落
    para_by_idx = {p['idx']: p for p in paragraphs}

    for p in paragraphs:
        idx = p.get('idx', 0)
        if idx < start or idx > end:
            continue
        text = p.get('text', '').strip()

        # 插入图片块（在本段落文字之前）
        for fig in fig_map.get(idx, []):
            fname = fig.get('filename', '')
            ext = Path(fname).suffix.lower()
            # 找图题：当前段落或下一段落是否以"图"开头
            caption = ''
            for nidx in [idx, idx+1, idx+2]:
                np_ = para_by_idx.get(nidx, {})
                nt = np_.get('text', '').strip()
                if re.match(r'^图\s*\d', nt):
                    caption = nt
                    break
            if ext == '.svg':
                # SVG 跳过，LaTeX 不直接支持
                continue
            content.append({
                "type": "figure",
                "embed": fig.get('rId', ''),
                "path": f"figures/{fname}",
                "caption": caption,
            })

        # 插入表格块（表格紧跟在 before_para == idx 的段落之后）
        for tbl in tbl_map.get(idx, []):
            rows = tbl.get('rows', [])
            if not rows:
                continue
            # 找表题：当前段落文字或下一段（"表X..."开头）
            caption = ''
            for nidx in [idx, idx+1, idx+2]:
                np_ = para_by_idx.get(nidx, {})
                nt = np_.get('text', '').strip()
                if re.match(r'^表\s*\d', nt):
                    caption = nt
                    break
            content.append({
                "type": "table",
                "caption": caption,
                "rows": rows,
            })

        if not text:
            continue

        # 跳过图题行（已并入 figure 块）
        if re.match(r'^图\s*\d', text):
            continue

        if idx in sec_map:
            sec = sec_map[idx]
            content.append({"type": "section", "level": sec['level'],
                             "number": sec['number'], "title": sec['title']})
        else:
            content.append({"type": "text", "content": text})

    return content


def llm_parse(raw_json_path, output_dir=None):
    raw_path = Path(raw_json_path).resolve()
    raw = json.loads(raw_path.read_text(encoding='utf-8'))

    if output_dir is None:
        output_dir = raw_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paragraphs = raw.get('paragraphs', [])
    tables = raw.get('tables', [])
    figures = raw.get('figures', [])

    print(f"✅ 读取: {len(paragraphs)}段落 {len(tables)}表格 {len(figures)}图片")

    # Step 1: 发骨架给 LLM
    skeleton = build_skeleton(paragraphs, max_lines=300)
    user_prompt = USER_TMPL.format(n=len(paragraphs), skeleton=skeleton)
    print(f"📤 骨架 prompt: {len(user_prompt):,} 字符")

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    base_url = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')

    raw_output = call_llm(SYSTEM, user_prompt, api_key, base_url)
    print(f"📥 LLM 返回: {len(raw_output):,} 字符")

    if not raw_output.strip():
        raise ValueError("LLM 返回空")

    cleaned = re.sub(r'^```[a-z]*\n?', '', raw_output.strip())
    cleaned = re.sub(r'\n?```$', '', cleaned)
    # JSON 不允许前导零整数（如 0004），替换为合法数字
    cleaned = re.sub(r':\s*0+(\d+)', lambda m: ': ' + str(int(m.group(1))), cleaned)
    cleaned = re.sub(r'\[\s*0+(\d+)', lambda m: '[' + str(int(m.group(1))), cleaned)
    cleaned = re.sub(r',\s*0+(\d+)', lambda m: ', ' + str(int(m.group(1))), cleaned)

    try:
        struct = json.loads(cleaned)
    except json.JSONDecodeError as e:
        debug = output_dir / f"llm_raw_{raw_path.stem}.txt"
        debug.write_text(raw_output, encoding='utf-8')
        print(f"❌ JSON解析失败: {e}，原始输出: {debug}")
        raise

    # Step 2: Python 按 idx 范围填充内容
    para_by_idx = {p['idx']: p for p in paragraphs}

    # meta：从封面表格提取
    meta = extract_meta_from_tables(tables)

    # 摘要
    def range_text(r):
        if not r or r[0] is None: return ''
        return paras_text(paragraphs, r[0], r[1] or 99999)

    abstract_cn = range_text(struct.get('abstract_cn_range'))
    abstract_en = range_text(struct.get('abstract_en_range'))

    kw_cn_idx = struct.get('keywords_cn_para')
    kw_en_idx = struct.get('keywords_en_para')
    def parse_keywords(idx):
        if idx is None: return []
        p = para_by_idx.get(idx, {})
        t = p.get('text', '')
        t = re.sub(r'^关键词[：:\s]*', '', t)
        t = re.sub(r'^[Kk]ey\s*[Ww]ords[：:\s]*', '', t)
        return [k.strip() for k in re.split(r'[；;，,、\s]+', t) if k.strip()]

    keywords_cn = parse_keywords(kw_cn_idx)
    keywords_en = parse_keywords(kw_en_idx)

    # 章节（传入 figures_by_para 和 tables_by_para）
    figures_by_para = {}
    for fig in figures:
        pid = fig.get('para_idx')
        if pid is not None:
            figures_by_para.setdefault(pid, []).append(fig)

    # tables_by_para: before_para → [table, ...]
    # 只处理正文范围内的表格（过滤封面/答辩委员会等文档头部表格）
    chap_structs = struct.get('chapters', [])
    chap_ranges = []
    for i, cs in enumerate(chap_structs):
        cr = cs.get('content_range', [0, 9999])
        s = int(cr[0]) if cr[0] else 0
        e = int(cr[1]) if (len(cr) > 1 and cr[1]) else 9999
        chap_ranges.append((s, e, i))

    # 第一章最早的起始 para_idx
    first_chap_start = chap_ranges[0][0] if chap_ranges else 0

    tables_by_para = {}
    for tbl in tables:
        bp = tbl.get('before_para')
        if bp is not None and bp >= first_chap_start:
            tables_by_para.setdefault(bp, []).append(tbl)

    # 对 before_para 在所有章节范围之外的表格，分配给最近的章节（按 before_para 距离）
    def find_chap_for_para(bp):
        """返回 bp 所属的章节 index（用 chap_ranges 或最近章节）"""
        for s, e, ci in chap_ranges:
            if s <= bp <= e:
                return ci
        # 找最近的章节（before_para 最近的 start 或 end）
        best_ci, best_dist = 0, float('inf')
        for s, e, ci in chap_ranges:
            dist = min(abs(bp - s), abs(bp - e))
            if dist < best_dist:
                best_dist = dist
                best_ci = ci
        return best_ci

    # 将不在任何章节 content_range 内的表格重新绑定
    # 构建 chap_index → extra_tables 字典
    extra_tables_by_chap = {}  # chap_index → [(before_para, tbl), ...]
    for bp, tbls in list(tables_by_para.items()):
        ci = find_chap_for_para(bp)
        s, e, _ = chap_ranges[ci] if ci < len(chap_ranges) else (0, 9999, 0)
        if not (s <= bp <= e):
            # 该 bp 在这个章节范围外，加入 extra，在最后追加
            extra_tables_by_chap.setdefault(ci, []).extend([(bp, t) for t in tbls])
            del tables_by_para[bp]

    chapters = []
    for i, cs in enumerate(chap_structs):
        next_start = chap_structs[i+1]['content_range'][0] if i+1 < len(chap_structs) else 99999
        content = build_chapter_content(cs, paragraphs, next_start, figures_by_para, tables_by_para)
        # 追加本章范围外但最近的表格（按 before_para 排序）
        extras = sorted(extra_tables_by_chap.get(i, []), key=lambda x: x[0])
        for bp, tbl in extras:
            rows = tbl.get('rows', [])
            if rows:
                paras_dict = {p['idx']: p for p in paragraphs}
                caption = ''
                for nidx in [bp, bp+1, bp+2]:
                    nt = paras_dict.get(nidx, {}).get('text', '').strip()
                    if re.match(r'^表\s*\d', nt):
                        caption = nt
                        break
                content.append({"type": "table", "caption": caption, "rows": rows})
        chapters.append({
            "level": 1,
            "number": cs.get('number', ''),
            "title": cs.get('title', ''),
            "content": content
        })

    # 用 Python 直接查 Heading 段落，不依赖 LLM 给的 range（LLM 容易把目录条目当正文）
    def find_heading_range(keyword):
        """找 Heading 1 中含 keyword 的段落后面的内容范围"""
        HEADING_STYLES = {'Heading 1','Heading1','标题1','Title1','heading 1','Heading1'}
        start = None
        for p in paragraphs:
            style = p.get('style','')
            text = p.get('text','').strip()
            if start is None:
                if keyword in text and (style in HEADING_STYLES or style.startswith('Heading')):
                    start = p['idx'] + 1  # 标题本身不算内容
            else:
                if style in HEADING_STYLES or style.startswith('Heading'):
                    return start, p['idx'] - 1
        return (start, None) if start else (None, None)

    # 参考文献
    ref_start, ref_end = find_heading_range('参考文献')
    references = []
    if ref_start:
        for p in paras_in_range(paragraphs, ref_start, ref_end or 99999):
            t = p.get('text','').strip()
            if t and len(t) > 5:
                references.append(t)

    # 致谢 / 简历 / 声明（用 Python 查找，LLM range 作为 fallback）
    ack_start, ack_end = find_heading_range('致谢')
    acknowledgements = paras_text(paragraphs, ack_start, ack_end or 99999) if ack_start else range_text(struct.get('acknowledgements_range'))

    res_start, res_end = find_heading_range('个人简历')
    resume = paras_text(paragraphs, res_start, res_end or 99999) if res_start else range_text(struct.get('resume_range'))

    sta_start, sta_end = find_heading_range('声明')
    statement = paras_text(paragraphs, sta_start, sta_end or 99999) if sta_start else range_text(struct.get('statement_range'))

    # figures_map
    figures_map = {f['rId']: {'filename': f['filename'], 'path': f"figures/{f['filename']}"} for f in figures}

    parsed = {
        "meta": meta,
        "abstract_cn": abstract_cn,
        "keywords_cn": keywords_cn,
        "abstract_en": abstract_en,
        "keywords_en": keywords_en,
        "chapters": chapters,
        "references": references,
        "acknowledgements": acknowledgements,
        "resume": resume,
        "statement": statement,
        "supervisor_comment": "",
        "defense_resolution": "",
        "figures_list": False,
        "tables_list": False,
        "figures": figures_map,
    }

    stem = raw_path.stem.replace('raw_', '', 1)
    out_path = output_dir / f"parsed_{stem}.json"
    out_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n✅ 完成 → {out_path}")
    print(f"   标题: {meta.get('title','?')}")
    print(f"   作者: {meta.get('author','?')}  导师: {meta.get('supervisor','?')}")
    print(f"   章节: {len(chapters)}  参考文献: {len(references)}")
    for ch in chapters:
        print(f"   [{ch['number']}] {ch['title']}  ({len(ch['content'])}块)")
    return parsed


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 llm_parse.py <raw_xxx.json> [output_dir]")
        sys.exit(1)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else str(Path(sys.argv[1]).parent)
    llm_parse(sys.argv[1], out_dir)
