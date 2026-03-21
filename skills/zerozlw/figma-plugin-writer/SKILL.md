# SKILL.md — Figma Plugin Writer

## 概述

通过编写 Figma 插件代码，实现对 Figma 文件的自动化设计。每次更新 `code.js` 后通知用户触发插件执行。

## 使用前配置

用户需要告诉 agent 以下信息（在对话中或通过 TOOLS.md）：

1. **插件目录路径** — Figma 插件所在文件夹（含 code.js 和 manifest.json）
2. **代码文件** — 通常是 `code.js`
3. **目标 Figma 文件** — 可选，用于上下文说明

示例配置（放入 agent 的 TOOLS.md）：
```markdown
## Figma Plugin Writer
**插件目录：** ~/Desktop/my-figma-plugin/
**代码文件：** code.js
```

## 工作流程

1. **接收需求** — 用户描述要设计的内容
2. **编写插件代码** — 更新 `code.js`，包含要绘制的设计元素
3. **通知用户** — 告诉用户"代码已更新，请运行插件：Plugins → Development → 插件名"
4. **等待反馈** — 用户运行后反馈效果，根据反馈迭代

## Figma Plugin API 参考

### 字体加载（必须在创建文字前执行）

```js
await figma.loadFontAsync({ family: "Inter", style: "Regular" });
await figma.loadFontAsync({ family: "Inter", style: "Medium" });
await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });
await figma.loadFontAsync({ family: "Inter", style: "Bold" });
```

### 创建 Frame（画框/容器）

```js
var frame = figma.createFrame();
frame.name = "MyFrame";
frame.resize(width, height);
frame.cornerRadius = 12;
frame.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
frame.x = 0;
frame.y = 0;
```

### 创建文字

```js
var text = figma.createText();
text.characters = "Hello World";
text.fontSize = 16;
text.fontName = { family: "Inter", style: "Regular" };
text.fills = [{ type: "SOLID", color: { r: 0, g: 0, b: 0 } }];
```

### 创建矩形

```js
var rect = figma.createRectangle();
rect.resize(100, 50);
rect.fills = [{ type: "SOLID", color: { r: 0.9, g: 0.2, b: 0.2 } }];
rect.cornerRadius = 8;
```

### 节点嵌套

```js
frame.appendChild(text);       // text 变成 frame 的子节点
parentPage.appendChild(frame); // frame 放到页面上
```

### 阴影效果

```js
frame.effects = [{
  type: "DROP_SHADOW",
  color: { r: 0, g: 0, b: 0, a: 0.1 },
  offset: { x: 0, y: 4 },
  radius: 12,
  spread: 0,
  visible: true,
  blendMode: "NORMAL",
}];
```

### 描边

```js
frame.strokes = [{ type: "SOLID", color: { r: 0.8, g: 0.8, b: 0.8 } }];
frame.strokeWeight = 1;
```

### 文字对齐

```js
text.textAlignHorizontal = "CENTER"; // LEFT | CENTER | RIGHT | JUSTIFIED
text.textAlignVertical = "CENTER";   // TOP | CENTER | BOTTOM
```

### 自动布局（Frame 内）

```js
frame.layoutMode = "VERTICAL"; // 或 "HORIZONTAL"
frame.primaryAxisAlignItems = "CENTER";   // MIN | CENTER | MAX | SPACE_BETWEEN
frame.counterAxisAlignItems = "CENTER";
frame.paddingTop = 16;
frame.paddingBottom = 16;
frame.paddingLeft = 16;
frame.paddingRight = 16;
frame.itemSpacing = 8;
```

### 切换页面

```js
// dynamic-page 模式下必须用异步方法
var pages = figma.root.children;
var targetPage = pages[pages.length - 1];
await figma.setCurrentPageAsync(targetPage);
```

### 清空页面内容

```js
var old = targetPage.children.slice();
for (var i = 0; i < old.length; i++) {
  old[i].remove();
}
```

### 视口操作

```js
figma.viewport.scrollAndZoomIntoView([frame]);
```

### 通知

```js
figma.notify("Done!", { timeout: 3000 });
figma.notify("ERROR: " + e.message, { timeout: 10000 });
```

### 获取页面信息

```js
var pages = figma.root.children;
var count = pages.length;
var pageName = pages[0].name;
```

## 代码模板

```js
async function main() {
  try {
    // 1. 加载字体
    await figma.loadFontAsync({ family: "Inter", style: "Regular" });
    await figma.loadFontAsync({ family: "Inter", style: "Bold" });

    // 2. 获取目标页面
    var pages = figma.root.children;
    var target = pages[pages.length - 1];
    await figma.setCurrentPageAsync(target);

    // 3. 清空旧内容
    var old = target.children.slice();
    for (var i = 0; i < old.length; i++) old[i].remove();

    // 4. 创建设计...
    var frame = figma.createFrame();
    frame.name = "Screen";
    frame.resize(375, 812);
    frame.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
    frame.x = 0;
    frame.y = 0;
    target.appendChild(frame);

    // 5. 完成
    figma.viewport.scrollAndZoomIntoView([frame]);
    figma.notify("Design complete!", { timeout: 3000 });

  } catch (e) {
    figma.notify("ERROR: " + e.message, { timeout: 10000 });
  }
}

main();
```

## 重要踩坑记录

### documentAccess: "dynamic-page" 模式
manifest.json 中如果有 `"documentAccess": "dynamic-page"`：
- ❌ `figma.currentPage = page` → ✅ `await figma.setCurrentPageAsync(page)`
- ❌ `figma.getNodeById()` → ✅ `await figma.getNodeByIdAsync()`
- ❌ `figma.closePlugin()` → ✅ `figma.closePluginAsync()`

### 容错策略
- 所有代码必须包在 `try-catch` 中
- 错误时用 `figma.notify("ERROR: " + e.message, { timeout: 10000 })` 显示
- 不要在文字中使用 emoji（字体可能不支持该 glyph）
- 不要自动调用 `figma.closePlugin()`（让用户手动关闭）

### 免费用户限制
- 最多 3 个 Pages，不要创建新 Page
- 在现有 Page 内操作（清空后重建）

### 字体说明
- 默认使用 Inter（Figma 内置字体）
- 支持的样式："Regular"、"Medium"、"Semi Bold"、"Bold"
- 如需其他字体，用户需先在 Figma 中安装
- 颜色用 `{ r, g, b }` 格式，值域 0-1

## 迭代模式

每次设计迭代时：
1. 清空目标 Page 内的旧元素：`page.children.slice().forEach(c => c.remove())`
2. 重新创建新设计
3. 通知用户重新运行插件
