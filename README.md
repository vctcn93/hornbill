# 犀鸟 (Hornbill)

> 给犀牛除虫的鸟 — Rhino 8 Python 插件开发框架

一套经过实战验证的 Rhino 8 Python 插件开发模板，包含项目骨架、一键安装脚本、多语言系统、Eto.Forms UI 模式和 Python.NET 避坑指南。

## 快速开始

```bash
# 1. 复制模板
cp -r templates/ my-plugin/
cd my-plugin

# 2. 改插件名
# 编辑 install.bat 里的 PLUGIN_NAME
# 编辑 plugin.rhproj 里的 identity.name

# 3. 写你的代码
# src/core/     — 核心逻辑
# src/forms/    — UI 对话框
# cmd/          — Rhino 命令入口
# configs/      — 配置文件

# 4. 双击 install.bat
```

## 项目结构

```
my-plugin/
├── install.bat              # 一键安装（检测→镜像→依赖→编译→安装）
├── requirements.txt         # 第三方依赖（锁定版本）
├── plugin.rhproj            # Rhino 项目文件
├── configs/                 # 配置入口（用户只改这里）
│   ├── urls.ini
│   ├── lang_en.ini
│   └── lang_cn.ini
├── cmd/                     # 命令入口
├── src/
│   ├── core/                # 核心逻辑（打包进 .rhp）
│   └── forms/               # UI 对话框（打包进 .rhp）
└── res/                     # 静态资源（打包进 shared/）
    ├── icons/
    └── gradients/
```

## 核心特性

- **多语言** — `lang.py` + `lang_*.ini`，自动检测 Rhino 语言
- **Config 系统** — `configs/` 维护 → `install.bat` 同步 → `src/core/` 读取
- **Ponytail 强制** — 内置 Ponytail full 级精简规则
- **Python.NET 坑** — 6 个常见陷阱及修复方案
- **Brainstorming Gate** — 写代码前强制需求确认

## 前置条件

- Rhino 8（已安装并至少运行过一次）
- Windows 10/11
- 网络连接（首次安装 pip 依赖需要）

## 文档

完整文档见 [SKILL.md](SKILL.md)

## License

MIT
