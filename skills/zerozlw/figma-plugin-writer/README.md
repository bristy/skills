# Figma Plugin Writer Skill

> 通过编写 Figma 插件代码，实现对 Figma 文件的自动化设计。

## 功能

- 自动创建 UI 设计稿（画框、文字、矩形、阴影等）
- 生成完整的 Design System 组件库
- 批量创建多屏幕原型
- 修改已有设计内容
- 自动排版和配色

## 前置要求

1. **Figma 桌面端**（用于运行插件）
2. **一个 Figma Plugin 项目**（通过 Figma 菜单创建：Plugins → Development → New Plugin）
3. 插件必须有 `code.js` 和 `manifest.json` 两个文件

## 安装

1. 在 Figma 中创建一个新插件：`Plugins → Development → New Plugin` → 选择 "Figma design" → "Run once"
2. 记下生成的插件目录路径
3. 将本 skill 的 `SKILL.md` 放到你的 agent 的 skills 目录下
4. 在 agent 配置中指定插件路径（见下方配置说明）

## 配置

在你的 agent 的 `TOOLS.md` 中添加：

```markdown
## Figma Plugin Writer

**插件目录：** /path/to/your/figma-plugin/
**代码文件：** code.js
**Skill 文件：** /path/to/skills/figma-plugin-writer/SKILL.md
```

## 工作流程

```
用户描述需求 → Agent 编写 code.js → 通知用户运行插件 → 用户反馈 → 迭代
```

具体步骤：
1. 用户在对话中描述要设计的内容（如"帮我画一个登录页面"）
2. Agent 修改插件目录下的 `code.js` 文件
3. Agent 通知用户：`Plugins → Development → 你的插件名`
4. 用户在 Figma 中运行插件查看效果
5. 用户反馈修改意见，Agent 迭代更新

## API 速查

详细的 Figma Plugin API 用法见 [SKILL.md](./SKILL.md)。

核心操作：
- `figma.createFrame()` — 创建画框
- `figma.createText()` — 创建文字
- `figma.createRectangle()` — 创建矩形
- `await figma.loadFontAsync()` — 加载字体（必须先加载再创建文字）
- `await figma.setCurrentPageAsync()` — 切换页面（dynamic-page 模式）
- `figma.viewport.scrollAndZoomIntoView()` — 视口定位
- `figma.notify()` — 显示通知

## 示例

查看 [examples/](./examples/) 目录中的示例：
- `01-basic-screen.js` — 基础屏幕创建
- `02-design-system.js` — Design System 组件库
- `03-multi-screen-app.js` — 多屏幕 App 原型

## 注意事项

- Figma 免费用户最多 3 个 Pages
- 字体必须先加载再使用（`await figma.loadFontAsync()`）
- 如果 manifest 有 `"documentAccess": "dynamic-page"`，必须用异步方法
- 所有代码包在 `try-catch` 中，错误会通过 `figma.notify()` 显示
- 不要在文字中使用 emoji（字体可能不支持）

## License

MIT
