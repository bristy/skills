---
name: eps
description: Bilingual EPS / PS / EPSF skill for local conversion, online SVG export, and metadata inspection using Ghostscript WASM / 双语 EPS / PS / EPSF 技能，支持本地转换、在线 SVG 导出和元数据解析
user-invocable: true
---

# EPS Tool

English:
Convert and inspect EPS / PS / EPSF files. Local conversion runs through Ghostscript WASM. Use the public web viewer for online inspection and SVG export.

中文：
用于转换和解析 EPS / PS / EPSF 文件。本地转换基于 Ghostscript WASM；在线预览、解析和 SVG 导出请使用公开网页工具。

## Public Service / 公开服务

- Web viewer / 在线工具: `https://eps.futrixdev.com`
- Skill endpoint / 技能地址: `https://eps.futrixdev.com/api/skill.md`
- Installer / 安装脚本: `https://eps.futrixdev.com/api/install.sh`

## Commands / 命令

### Convert EPS to another format / 转换 EPS 到其他格式

```bash
node cli/eps-cli.mjs convert <file.eps> --format <png|jpg|pdf> [--dpi <number>] [--output <path>]
```

English:
- `--format` output format: `png` (default, lossless), `jpg` (compressed), `pdf` (vector)
- `--dpi` resolution 36–1200; use 150 for web and 300 for print
- `--output` output path; auto-generated if omitted
- CLI conversion supports `png`, `jpg`, and `pdf`

中文：
- `--format` 输出格式：`png`（默认，无损）、`jpg`（压缩）、`pdf`（矢量）
- `--dpi` 分辨率范围 36–1200；网页场景建议 150，打印建议 300
- `--output` 输出路径；不传时自动生成
- 命令行转换当前支持 `png`、`jpg` 和 `pdf`

### View EPS metadata / 查看 EPS 元数据

```bash
node cli/eps-cli.mjs info <file.eps>
```

English:
Shows title, creator, BoundingBox, dimensions (pt/mm), PS version, and fonts.

中文：
可查看标题、创建者、BoundingBox、尺寸（pt/mm）、PS 版本和字体信息。

### Set server URL / 设置服务地址

```bash
eps config:set https://eps.futrixdev.com --global
```

English:
Use the hosted public service above as the default server.

中文：
推荐把上面的公开服务地址设置为默认服务端。

### Open web viewer / 打开网页工具

```bash
node cli/eps-cli.mjs view --server https://eps.futrixdev.com
```

English:
The web viewer supports EPS / PS / EPSF online inspection and export to PNG / JPG / SVG / PDF.

中文：
网页工具支持 EPS / PS / EPSF 在线查看、解析，并导出 PNG / JPG / SVG / PDF。

## Usage Guidelines / 使用建议

English:
- Use `convert` for local conversion
- Use `info` for metadata inspection
- Use the web viewer for SVG export and visual workflows

中文：
- 本地格式转换用 `convert`
- 元数据解析用 `info`
- 需要 SVG 导出或可视化流程时使用网页工具
