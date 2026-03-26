# 技能进化数据表结构

## skill_usage 表
记录每次技能调用的详细数据

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| timestamp | TEXT | 调用时间 (ISO 8601) |
| skill_name | TEXT | 技能名称 |
| query | TEXT | 用户查询内容 |
| response_time_ms | INTEGER | 响应时间(毫秒) |
| success | BOOLEAN | 是否成功 |
| user_feedback | INTEGER | 用户反馈 (-1/0/1) |
| case_references | TEXT | 引用的案例ID (JSON数组) |
| created_at | TEXT | 记录创建时间 |

## skill_stats 表
按日统计技能使用数据

| 字段 | 类型 | 说明 |
|------|------|------|
| date | TEXT | 日期 (YYYY-MM-DD) |
| skill_name | TEXT | 技能名称 |
| total_calls | INTEGER | 总调用次数 |
| success_count | INTEGER | 成功次数 |
| avg_response_time_ms | REAL | 平均响应时间 |
| positive_feedback | INTEGER | 正面反馈数 |
| negative_feedback | INTEGER | 负面反馈数 |
| unique_cases_referenced | INTEGER | 引用的不同案例数 |
