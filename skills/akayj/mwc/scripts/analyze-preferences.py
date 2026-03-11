#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#     "polars>=1.0.0",
#     "duckdb>=1.0.0",
# ]
# ///
"""
偏好分析脚本
分析用户壁纸评分数据，生成统计报告
"""

import polars as pl
import duckdb
from pathlib import Path
from datetime import datetime

PREFERENCES_FILE = Path.home() / "wallpaper-daily" / "preferences.parquet"


def load_preferences() -> pl.DataFrame | None:
    """加载偏好数据"""
    if not PREFERENCES_FILE.exists():
        print("❌ 偏好数据文件不存在")
        print("提示：先使用换壁纸功能并评分，积累数据后再分析")
        return None
    
    try:
        return pl.read_parquet(PREFERENCES_FILE)
    except Exception as e:
        print(f"❌ 读取数据失败：{e}")
        return None


def analyze_with_polars(df: pl.DataFrame) -> None:
    """使用 polars 分析"""
    print("\n" + "=" * 60)
    print("📊 Polars 统计分析")
    print("=" * 60)
    
    # 基础统计
    print(f"\n📈 数据概览:")
    print(f"  总评分数：{len(df)}")
    print(f"  数据时间范围：{df['date'].min()} ~ {df['date'].max()}")
    
    # 平均评分
    avg_rating = df['rating'].mean()
    print(f"  平均评分：{avg_rating:.2f}/10")
    
    # 评分分布
    print(f"\n⭐ 评分分布:")
    rating_dist = df.group_by('rating').agg(
        pl.col('rating').count().alias('count')
    ).sort('rating')
    for row in rating_dist.iter_rows():
        bar = "█" * row[1]
        print(f"  {row[0]}分：{bar} ({row[1]}次)")
    
    # 分类偏好
    print(f"\n🏷️ 分类偏好:")
    category_stats = df.group_by('category').agg(
        pl.col('rating').mean().alias('avg_rating'),
        pl.col('rating').count().alias('count')
    ).sort('avg_rating', descending=True)
    
    for row in category_stats.iter_rows():
        stars = "⭐" * int(row[1] / 2)
        print(f"  {row[0]:10s}: {stars} ({row[1]:.1f}分，{row[2]}次)")
    
    # 色调偏好
    print(f"\n🎨 色调偏好:")
    tone_stats = df.group_by('color_tone').agg(
        pl.col('rating').mean().alias('avg_rating'),
        pl.col('rating').count().alias('count')
    ).sort('avg_rating', descending=True)
    
    for row in tone_stats.iter_rows():
        if row[0] != "unknown":
            print(f"  {row[0]:10s}: {row[1]:.1f}分 ({row[2]}次)")
    
    # 标签分析
    print(f"\n🔖 热门标签:")
    all_tags = []
    for tags in df['tags']:
        all_tags.extend(tags)
    
    if all_tags:
        tag_counts = pl.DataFrame({'tag': all_tags}).group_by('tag').agg(
            pl.col('tag').count().alias('count')
        ).sort('count', descending=True).head(10)
        
        for i, row in enumerate(tag_counts.iter_rows(), 1):
            print(f"  {i:2d}. #{row[0]} ({row[1]}次)")
    
    # 时间趋势
    print(f"\n📅 近期趋势 (最近 7 天):")
    recent = df.filter(
        pl.col('date') >= datetime.now().timestamp() - 7 * 24 * 3600
    )
    if len(recent) > 0:
        recent_avg = recent['rating'].mean()
        overall_avg = df['rating'].mean()
        trend = "↑" if recent_avg > overall_avg else "↓" if recent_avg < overall_avg else "→"
        print(f"  近期平均：{recent_avg:.2f}分 {trend} (总体：{overall_avg:.2f}分)")
    else:
        print("  最近 7 天无评分")


def analyze_with_duckdb(df: pl.DataFrame) -> None:
    """使用 duckdb 进行高级分析"""
    print("\n" + "=" * 60)
    print("🦆 DuckDB 深度分析")
    print("=" * 60)
    
    # 创建临时表
    con = duckdb.connect()
    con.register('preferences', df)
    
    # 最佳壁纸
    print("\n🏆 评分最高的壁纸:")
    query = """
        SELECT wallpaper_path, rating, category, color_tone, 
               array_to_string(tags, ', ') as tags
        FROM preferences
        WHERE rating >= 8
        ORDER BY rating DESC, date DESC
        LIMIT 5
    """
    result = con.execute(query).fetchdf()
    for i, row in result.iterrows():
        print(f"  {i+1}. {row['wallpaper_path'].split('/')[-1]}")
        print(f"     评分：{row['rating']} | 分类：{row['category']} | 色调：{row['color_tone']}")
        if row['tags']:
            print(f"     标签：{row['tags']}")
    
    # 分类组合分析
    print("\n🔍 分类 + 色调组合分析:")
    query = """
        SELECT category, color_tone, 
               ROUND(AVG(rating), 2) as avg_rating,
               COUNT(*) as count
        FROM preferences
        WHERE color_tone != 'unknown'
        GROUP BY category, color_tone
        HAVING COUNT(*) >= 2
        ORDER BY avg_rating DESC
        LIMIT 8
    """
    result = con.execute(query).fetchdf()
    for i, row in result.iterrows():
        print(f"  {row['category']:10s} + {row['color_tone']:6s}: {row['avg_rating']}分 ({row['count']}次)")
    
    # 相关性分析
    print("\n📊 评分相关性分析:")
    query = """
        SELECT 
            CORR(rating, EXTRACT(EPOCH FROM date)) as time_rating_corr
        FROM preferences
    """
    result = con.execute(query).fetchone()
    if result[0]:
        corr = float(result[0])
        if abs(corr) > 0.5:
            trend = "偏好提升" if corr > 0 else "偏好下降"
            print(f"  时间 - 评分相关性：{corr:.2f} ({trend})")
        else:
            print(f"  时间 - 评分相关性：{corr:.2f} (无明显趋势)")
    
    # 推荐权重计算
    print("\n⚖️ 推荐权重计算:")
    query = """
        SELECT 
            category,
            AVG(rating) as base_score,
            COUNT(*) as confidence,
            AVG(rating) * (1 + 0.1 * LN(COUNT(*) + 1)) as weighted_score
        FROM preferences
        GROUP BY category
        ORDER BY weighted_score DESC
    """
    result = con.execute(query).fetchdf()
    for i, row in result.iterrows():
        print(f"  {row['category']:10s}: 基础分 {row['base_score']:.2f} × 置信度 = {row['weighted_score']:.2f}")
    
    con.close()


def generate_report() -> None:
    """生成完整报告"""
    df = load_preferences()
    if df is None:
        return
    
    analyze_with_polars(df)
    analyze_with_duckdb(df)
    
    print("\n" + "=" * 60)
    print("💡 智能建议")
    print("=" * 60)
    
    # 基于分析给出建议
    avg_rating = df['rating'].mean()
    top_category = df.group_by('category').agg(
        pl.col('rating').mean().alias('avg')
    ).sort('avg', descending=True).row(0)[0]
    
    print(f"\n  ✓ 你的平均评分：{avg_rating:.1f}/10")
    print(f"  ✓ 最喜爱的分类：{top_category}")
    print(f"  ✓ 建议：多尝试 {top_category} 类壁纸，评分可能会更高")
    
    if avg_rating < 6:
        print(f"  ⚠ 提示：近期壁纸满意度较低，建议调整推荐策略")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="分析壁纸评分数据，生成偏好统计报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/analyze-preferences.py
  uv run scripts/analyze-preferences.py --json
"""
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()
    
    if args.json:
        df = load_preferences()
        if df is None:
            return 1
        import json
        stats = {
            "total_ratings": len(df),
            "avg_rating": float(df['rating'].mean()),
            "top_category": df.group_by('category').agg(
                pl.col('rating').mean().alias('avg')
            ).sort('avg', descending=True).row(0)[0]
        }
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0
    
    print("🦞 Mac 壁纸偏好分析报告")
    print(f"数据文件：{PREFERENCES_FILE}")
    print(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    generate_report()
    return 0


if __name__ == "__main__":
    exit(main())
