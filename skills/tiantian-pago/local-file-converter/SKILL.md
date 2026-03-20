# file-converter Skill

本地文件转换技能，使用命令行工具实现 1000+ 格式互转。

## 能力

- **图片**: JPG, PNG, WebP, HEIC, GIF, BMP, TIFF, SVG 等
- **视频**: MP4, AVI, MKV, MOV, WebM, GIF 等
- **音频**: MP3, FLAC, WAV, AAC, OGG, M4A 等
- **文档**: PDF, DOCX, DOC, EPUB, MOBI, TXT, Markdown 等
- **数据**: JSON, YAML, XML, CSV 等

## 底层工具

本技能调用以下系统工具：

| 工具 | 用途 | 状态 |
|------|------|------|
| `ffmpeg` | 音视频转换 | ✅ 已安装 (v7.1.13) |
| `imagemagick` | 图片转换 | ✅ 已安装 (v7.1.11-43) |
| `libreoffice` | 文档转换 | ✅ 已安装 (v25.2.3) |
| `pandoc` | 文档/标记转换 | ✅ 已安装 (v3.1.11) |
| `calibre` | 电子书转换 | 按需安装 |

### 安装命令（如需）

```bash
# Debian/Ubuntu
sudo apt install ffmpeg imagemagick libreoffice pandoc calibre

# macOS
brew install ffmpeg imagemagick libreoffice pandoc
brew install --cask calibre
```

## 使用方式

用户说类似：
- "把这个图片转成 WebP"
- "将 video.mp4 转换成 GIF"
- "把 document.docx 转为 PDF"
- "转换这本书为 EPUB 格式"

技能自动：
1. 识别源文件和目标格式
2. 选择合适的转换工具
3. 执行转换命令
4. 返回结果文件路径

## 命令参考

### 图片转换 (ImageMagick)
```bash
# 基本转换
convert input.png output.webp
convert image.jpg image.png

# 批量转换
mogrify -format webp *.png

# 调整尺寸 + 转换
convert input.jpg -resize 1920x1080 output.jpg
```

### 视频/音频转换 (FFmpeg)
```bash
# 视频转 GIF
ffmpeg -i input.mp4 -vf "fps=10,scale=640:-1" output.gif

# 视频格式转换
ffmpeg -i input.mp4 -c:v libx265 output.mkv

# 提取音频
ffmpeg -i video.mp4 -q:a 0 -map a output.mp3

# 音频格式转换
ffmpeg -i input.wav -b:a 320k output.mp3
```

### 文档转换 (LibreOffice)
```bash
# Office 转 PDF
libreoffice --headless --convert-to pdf document.docx

# PDF 转其他格式
libreoffice --headless --convert-to docx document.pdf
```

### 文档/标记转换 (Pandoc)
```bash
# Markdown 转 PDF
pandoc input.md -o output.pdf

# Markdown 转 DOCX
pandoc input.md -o output.docx

# HTML 转 Markdown
pandoc input.html -t markdown -o output.md
```

### 电子书转换 (Calibre)
```bash
# EPUB 转 MOBI
ebook-convert input.epub output.mobi

# EPUB 转 PDF
ebook-convert input.epub output.pdf
```

## 文件路径

- **工作目录**: `/home/pago/.openclaw/workspace`
- **转换输出**: `/home/pago/.openclaw/workspace/converted/`
- **临时文件**: 自动清理

## 使用示例

**用户说**: "把这张图转成 WebP"
**技能执行**:
```bash
convert /path/to/image.png /home/pago/.openclaw/workspace/converted/image.webp
```

**用户说**: "把这个视频转成 GIF"
**技能执行**:
```bash
ffmpeg -i /path/to/video.mp4 -vf "fps=10,scale=640:-1" /home/pago/.openclaw/workspace/converted/video.gif
```

**用户说**: "把文档转成 PDF"
**技能执行**:
```bash
libreoffice --headless --convert-to pdf /path/to/doc.docx --outdir /home/pago/.openclaw/workspace/converted/
```

## 注意事项

- ⚠️ **大文件转换**可能需要较长时间
- ⚠️ **视频转换**消耗 CPU，建议在空闲时进行
- ⚠️ **有损转换**可能降低质量（如视频压缩、图片重编码）
- ⚠️ **HEIC 格式**需要 `libheif` 支持
- ✅ **批量转换**建议逐个处理，避免并发过高

## 状态检查

运行以下命令验证工具可用：
```bash
ffmpeg -version | head -1
convert --version | head -1
libreoffice --version | head -1
pandoc --version | head -1
```
