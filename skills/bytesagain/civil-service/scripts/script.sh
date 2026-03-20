#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Civil Service Exam Helper (公务员考试助手)
# Version 3.0.0
# Powered by BytesAgain | bytesagain.com | hello@bytesagain.com
# ============================================================================

VERSION="3.0.0"
BRAND="Powered by BytesAgain | bytesagain.com | hello@bytesagain.com"
DATA_DIR="${HOME}/.local/share/civil-service"
HISTORY_FILE="${DATA_DIR}/history.jsonl"
LOG_FILE="${DATA_DIR}/civil-service.log"

mkdir -p "$DATA_DIR"

log_entry() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

show_header() {
    echo "============================================"
    echo "  📝 公务员考试助手 v${VERSION}"
    echo "  ${BRAND}"
    echo "============================================"
    echo ""
}

# ── Question Banks ──

# 常识判断
declare -a CHANGSHI_Q=(
    "我国最高国家权力机关是？|A.国务院|B.全国人民代表大会|C.最高人民法院|D.中央军委|B"
    "中华人民共和国成立于哪一年？|A.1945|B.1948|C.1949|D.1950|C"
    "我国现行宪法是哪一年通过的？|A.1954|B.1975|C.1978|D.1982|D"
    "中国共产党第一次全国代表大会召开地点是？|A.北京|B.上海|C.广州|D.武汉|B"
    "马克思主义哲学的基本问题是？|A.实践与认识|B.物质与意识|C.对立与统一|D.现象与本质|B"
    "我国的根本政治制度是？|A.政治协商制度|B.人民代表大会制度|C.民族区域自治|D.基层群众自治|B"
    "依法治国是党领导人民治理国家的？|A.基本路线|B.基本方略|C.根本方法|D.重要手段|B"
    "社会主义核心价值观中属于国家层面的是？|A.爱国敬业|B.自由平等|C.富强民主文明和谐|D.诚信友善|C"
)

# 言语理解
declare -a YANYU_Q=(
    "「不以规矩，不能成方圆」强调的是？|A.创新精神|B.规则意识|C.团结协作|D.个人自由|B"
    "「千里之行，始于足下」比喻？|A.路途遥远|B.事情从头做起|C.行走辛苦|D.旅途漫长|B"
    "「亡羊补牢」的近义词是？|A.未雨绸缪|B.防患未然|C.亡羊得牛|D.见兔顾犬|D"
    "「居安思危」告诉我们要？|A.安于现状|B.不思进取|C.未雨绸缪|D.杞人忧天|C"
    "「举一反三」表示？|A.做事犹豫|B.善于推理|C.反复无常|D.多此一举|B"
)

# 数量关系
declare -a SHULIANG_Q=(
    "甲乙两人从相距100公里的两地同时相向而行，甲每小时走6公里，乙每小时走4公里，几小时后相遇？|A.8|B.10|C.12|D.15|B"
    "一个水池有甲乙两个进水管，甲管单独注满需6小时，乙管单独注满需8小时，同时开两管需几小时注满？|A.3|B.3.43|C.4|D.4.5|B"
    "某商品打八折后售价为160元，原价是多少元？|A.180|B.192|C.200|D.210|C"
    "从1到100中，能被3整除的数有多少个？|A.30|B.33|C.34|D.36|B"
    "某班有50人，数学及格40人，语文及格42人，两科都及格至少有多少人？|A.30|B.32|C.35|D.38|B"
)

# 判断推理
declare -a PANDUAN_Q=(
    "所有的鱼都生活在水中，金鱼是鱼，所以金鱼生活在水中。这是什么推理？|A.归纳推理|B.演绎推理|C.类比推理|D.因果推理|B"
    "如果天下雨，地面就会湿。地面湿了，能否判断天下雨了？|A.能|B.不能|C.有时能|D.以上都不对|B"
    "甲说：我是诚实的。乙说：甲在说谎。如果只有一人说真话？|A.甲说真话|B.乙说真话|C.无法判断|D.都说真话|C"
    "1,4,9,16,25,?下一个数是？|A.30|B.33|C.36|D.49|C"
    "ABCD:EFGH等于IJKL:?|A.LMNO|B.MNOP|C.NOPQ|D.OPQR|B"
)

# 资料分析
declare -a ZILIAO_Q=(
    "2023年某市GDP为5000亿元，同比增长8%，2022年GDP约为多少亿元？|A.4500|B.4630|C.4700|D.4800|B"
    "某公司今年利润1200万元，去年800万元，增长率约为？|A.33%|B.40%|C.50%|D.60%|C"
    "某市人口500万，城镇化率60%，农村人口约为？|A.100万|B.150万|C.200万|D.300万|C"
)

get_questions_by_category() {
    local category="$1"
    case "$category" in
        changshi|常识)     declare -n arr=CHANGSHI_Q ;;
        yanyu|言语)        declare -n arr=YANYU_Q ;;
        shuliang|数量)     declare -n arr=SHULIANG_Q ;;
        panduan|判断)      declare -n arr=PANDUAN_Q ;;
        ziliao|资料)       declare -n arr=ZILIAO_Q ;;
        *)
            echo ""
            return 1
            ;;
    esac
    local count=${#arr[@]}
    if (( count == 0 )); then return 1; fi
    local idx=$(( RANDOM % count ))
    echo "${arr[$idx]}"
}

cmd_quiz() {
    local category="${1:-changshi}"
    show_header
    echo "▶ 模拟答题 — 类别：${category}"
    echo ""

    local question_data
    question_data=$(get_questions_by_category "$category")
    if [[ -z "$question_data" ]]; then
        echo "❌ 未知类别：${category}"
        echo "   可选：changshi(常识), yanyu(言语), shuliang(数量), panduan(判断), ziliao(资料)"
        return 1
    fi

    IFS='|' read -ra parts <<< "$question_data"
    local question="${parts[0]}"
    local opt_a="${parts[1]}"
    local opt_b="${parts[2]}"
    local opt_c="${parts[3]}"
    local opt_d="${parts[4]}"
    local answer="${parts[5]}"

    echo "  题目：${question}"
    echo ""
    echo "  ${opt_a}"
    echo "  ${opt_b}"
    echo "  ${opt_c}"
    echo "  ${opt_d}"
    echo ""
    echo "  ──────────────"
    echo "  ✅ 正确答案：${answer}"
    echo ""

    # Show the correct option text
    case "$answer" in
        A) echo "  → ${opt_a}" ;;
        B) echo "  → ${opt_b}" ;;
        C) echo "  → ${opt_c}" ;;
        D) echo "  → ${opt_d}" ;;
    esac

    # Record to history
    echo "{\"time\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"category\":\"${category}\",\"question\":\"${question}\",\"answer\":\"${answer}\"}" >> "$HISTORY_FILE"

    log_entry "QUIZ category=${category}"
}

cmd_score() {
    local answers="${1:?用法: civil-service score <answers>  例: ABCDBA}"
    show_header
    echo "▶ 评分"
    echo ""

    local total=${#answers}
    local correct=0

    # Simulate scoring against a fixed answer key
    local answer_key="BCDBCBBCBB"
    local key_len=${#answer_key}

    echo "  ── 评分结果 ──"
    echo ""
    printf "  %-6s %-8s %-8s %-8s\n" "题号" "你的答案" "正确答案" "结果"
    printf "  %-6s %-8s %-8s %-8s\n" "----" "------" "------" "----"

    for (( i=0; i<total; i++ )); do
        local your="${answers:$i:1}"
        local right="?"
        if (( i < key_len )); then
            right="${answer_key:$i:1}"
        fi
        local result="❌"
        if [[ "${your^^}" == "${right}" ]]; then
            result="✅"
            (( correct++ ))
        fi
        printf "  %-6s %-8s %-8s %-8s\n" "$((i+1))" "${your^^}" "$right" "$result"
    done

    echo ""
    echo "  总题数：${total}"
    echo "  正确数：${correct}"
    echo "  正确率：$(( correct * 100 / total ))%"

    local grade
    local pct=$(( correct * 100 / total ))
    if (( pct >= 90 )); then grade="优秀 🏆"
    elif (( pct >= 70 )); then grade="良好 👍"
    elif (( pct >= 60 )); then grade="及格 ✔️"
    else grade="需要加油 💪"
    fi
    echo "  评级：${grade}"

    log_entry "SCORE answers=${answers} correct=${correct}/${total}"
}

cmd_topics() {
    show_header
    echo "▶ 考试科目概览"
    echo ""

    echo "  ── 行政职业能力测验（行测）──"
    echo "  ├── 常识判断（changshi）    — 政治、法律、经济、科技等"
    echo "  ├── 言语理解（yanyu）       — 阅读理解、逻辑填空等"
    echo "  ├── 数量关系（shuliang）    — 数学运算、数字推理"
    echo "  ├── 判断推理（panduan）     — 图形推理、定义判断、逻辑判断"
    echo "  └── 资料分析（ziliao）      — 数据分析、图表阅读"
    echo ""
    echo "  ── 申论 ──"
    echo "  ├── 归纳概括题"
    echo "  ├── 综合分析题"
    echo "  ├── 提出对策题"
    echo "  ├── 应用文写作"
    echo "  └── 大作文"
    echo ""
    echo "  ── 题库统计 ──"
    echo "  常识判断题：${#CHANGSHI_Q[@]} 题"
    echo "  言语理解题：${#YANYU_Q[@]} 题"
    echo "  数量关系题：${#SHULIANG_Q[@]} 题"
    echo "  判断推理题：${#PANDUAN_Q[@]} 题"
    echo "  资料分析题：${#ZILIAO_Q[@]} 题"
    echo "  总计：$(( ${#CHANGSHI_Q[@]} + ${#YANYU_Q[@]} + ${#SHULIANG_Q[@]} + ${#PANDUAN_Q[@]} + ${#ZILIAO_Q[@]} )) 题"

    log_entry "TOPICS"
}

cmd_tips() {
    local topic="${1:-general}"
    show_header
    echo "▶ 备考技巧 — ${topic}"
    echo ""

    case "$topic" in
        changshi|常识)
            echo "  📚 常识判断备考技巧"
            echo ""
            echo "  1. 每天看新闻联播或人民日报，积累时政知识"
            echo "  2. 重点掌握宪法和行政法基本知识"
            echo "  3. 关注科技创新和重大科学发现"
            echo "  4. 了解中国历史上的重大事件和人物"
            echo "  5. 积累地理和文化常识"
            echo "  6. 用碎片时间刷题，广泛涉猎"
            ;;
        yanyu|言语)
            echo "  📖 言语理解备考技巧"
            echo ""
            echo "  1. 大量阅读政府工作报告和人民日报评论"
            echo "  2. 掌握常见成语和近义词辨析"
            echo "  3. 注意关联词和转折词，把握文章主旨"
            echo "  4. 阅读时注意首尾句和中心句"
            echo "  5. 排除法是言语理解的利器"
            echo "  6. 每天至少练习30道题保持手感"
            ;;
        shuliang|数量)
            echo "  🔢 数量关系备考技巧"
            echo ""
            echo "  1. 熟记常用公式：行程、工程、利润等"
            echo "  2. 掌握代入排除法，节省计算时间"
            echo "  3. 特殊值法是快速解题的关键"
            echo "  4. 多练习数字推理，找规律"
            echo "  5. 不要在难题上花太多时间"
            echo "  6. 先做有把握的题，难题最后做"
            ;;
        panduan|判断)
            echo "  🧩 判断推理备考技巧"
            echo ""
            echo "  1. 图形推理：注意对称、旋转、数量关系"
            echo "  2. 定义判断：抓住核心关键词"
            echo "  3. 类比推理：先确定关系类型"
            echo "  4. 逻辑判断：掌握充分必要条件"
            echo "  5. 学会画逻辑图辅助分析"
            echo "  6. 翻译推理口诀：前推后，否后推否前"
            ;;
        ziliao|资料)
            echo "  📊 资料分析备考技巧"
            echo ""
            echo "  1. 熟练掌握增长率、比重、倍数等概念"
            echo "  2. 学会快速阅读图表和数据"
            echo "  3. 估算能力比精确计算更重要"
            echo "  4. 先看问题再看材料，有的放矢"
            echo "  5. 截位法和特征数字法加快计算"
            echo "  6. 这部分正确率应争取90%以上"
            ;;
        *)
            echo "  📋 综合备考建议"
            echo ""
            echo "  1. 制定详细的复习计划并严格执行"
            echo "  2. 真题为王——近5年真题至少做3遍"
            echo "  3. 错题本必须有，定期回顾"
            echo "  4. 模考时严格计时：行测120分钟"
            echo "  5. 行测目标：总分70+分"
            echo "  6. 申论重视积累素材和模板"
            echo "  7. 保持良好作息，考前不熬夜"
            echo "  8. 考场技巧：先易后难，合理分配时间"
            ;;
    esac

    log_entry "TIPS topic=${topic}"
}

cmd_timer() {
    local minutes="${1:?用法: civil-service timer <minutes>}"
    show_header
    echo "▶ 计时器 — ${minutes} 分钟"
    echo ""

    if ! [[ "$minutes" =~ ^[0-9]+$ ]] || (( minutes > 180 )); then
        echo "❌ 分钟数无效（范围 1-180）"
        return 1
    fi

    local total_seconds=$(( minutes * 60 ))
    local start_epoch
    start_epoch=$(date +%s)
    local end_epoch=$(( start_epoch + total_seconds ))

    echo "  开始时间：$(date '+%H:%M:%S')"
    echo "  结束时间：$(date -d "@${end_epoch}" '+%H:%M:%S' 2>/dev/null || date -r "$end_epoch" '+%H:%M:%S' 2>/dev/null)"
    echo "  总时长：${minutes} 分钟"
    echo ""

    # Progress bar updates
    local interval=30
    if (( total_seconds < 60 )); then interval=5; fi

    local elapsed=0
    while (( elapsed < total_seconds )); do
        sleep "$interval"
        elapsed=$(( $(date +%s) - start_epoch ))
        local remaining=$(( total_seconds - elapsed ))
        if (( remaining < 0 )); then remaining=0; fi
        local pct=$(( elapsed * 100 / total_seconds ))
        if (( pct > 100 )); then pct=100; fi
        local bar_len=$(( pct / 5 ))
        local bar=""
        for (( b=0; b<20; b++ )); do
            if (( b < bar_len )); then bar+="█"; else bar+="░"; fi
        done
        local rem_min=$(( remaining / 60 ))
        local rem_sec=$(( remaining % 60 ))
        printf "\r  [%s] %3d%% — 剩余 %02d:%02d" "$bar" "$pct" "$rem_min" "$rem_sec"
    done

    echo ""
    echo ""
    echo "  ⏰ 时间到！"
    echo "  用时：${minutes} 分钟"

    log_entry "TIMER minutes=${minutes}"
}

cmd_history() {
    show_header
    echo "▶ 答题历史"
    echo ""

    if [[ ! -s "$HISTORY_FILE" ]]; then
        echo "  暂无答题记录"
        return 0
    fi

    local total
    total=$(wc -l < "$HISTORY_FILE")
    echo "  总答题数：${total}"
    echo ""

    echo "  ── 最近10条记录 ──"
    echo ""
    printf "  %-22s %-10s %-8s\n" "时间" "类别" "答案"
    printf "  %-22s %-10s %-8s\n" "----" "----" "----"

    tail -10 "$HISTORY_FILE" | while IFS= read -r line; do
        local ts cat ans
        ts=$(echo "$line" | grep -o '"time":"[^"]*"' | cut -d'"' -f4 | cut -c1-19)
        cat=$(echo "$line" | grep -o '"category":"[^"]*"' | cut -d'"' -f4)
        ans=$(echo "$line" | grep -o '"answer":"[^"]*"' | cut -d'"' -f4)
        printf "  %-22s %-10s %-8s\n" "$ts" "$cat" "$ans"
    done

    echo ""
    echo "  ── 类别统计 ──"
    for cat in changshi yanyu shuliang panduan ziliao; do
        local count
        count=$(grep -c "\"category\":\"${cat}\"" "$HISTORY_FILE" 2>/dev/null || echo 0)
        printf "  %-10s: %s 题\n" "$cat" "$count"
    done

    log_entry "HISTORY viewed"
}

cmd_help() {
    show_header
    cat <<EOF
用法: civil-service <command> [arguments]

命令:
  quiz <category>     随机出一道题 (changshi/yanyu/shuliang/panduan/ziliao)
  score <answers>     评分 (例: ABCDBA)
  topics              查看考试科目概览
  tips [topic]        备考技巧 (changshi/yanyu/shuliang/panduan/ziliao)
  timer <minutes>     计时器
  history             查看答题历史
  help                显示帮助

数据目录: ${DATA_DIR}
EOF
}

main() {
    local cmd="${1:-help}"
    shift || true

    case "$cmd" in
        quiz)       cmd_quiz "$@" ;;
        score)      cmd_score "$@" ;;
        topics)     cmd_topics ;;
        tips)       cmd_tips "$@" ;;
        timer)      cmd_timer "$@" ;;
        history)    cmd_history ;;
        help|--help|-h) cmd_help ;;
        *)
            echo "未知命令: ${cmd}"
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
