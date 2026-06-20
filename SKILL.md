# 犀鸟 (Hornbill) — Rhino 8 Python 插件开发框架

犀鸟给犀牛除虫。本 Skill 提供 Rhino 8 Python 插件开发的全套架构模式、脚手架模板、Python.NET 避坑指南和强制 Ponytail 精简规则。

---

## 0. Brainstorming Gate（强制）

**任何代码改动前，必须先用 `question` 工具确认需求。**

触发本 Skill 后，必须先问清楚：
- 这个功能要做什么？（一句话）
- 涉及哪些文件？（UI / 逻辑 / 数据）
- 有几种实现方式？（至少想两种，选最简的）

用多选 `question` 工具，一个消息可以带多个问题，让用户左右切换选项回答。不要一口气问太多开放式问题。用户确认后再动手写代码。

---

## 1. 项目骨架

```
my-plugin/
├── install.bat              # 一键安装脚本
├── requirements.txt         # 第三方依赖（锁定版本）
├── plugin.rhproj            # Rhino 项目文件
├── configs/                 # 配置入口（用户只改这里）
│   ├── urls.ini
│   ├── lang_en.ini
│   └── lang_cn.ini
├── cmd/                     # 命令入口（每个 .py 一个 Rhino 命令）
│   └── o_my_command.py
├── src/
│   ├── core/                # 核心逻辑（library path → 打包进 .rhp）
│   │   ├── __init__.py
│   │   └── lang.py          # 多语言模块
│   └── forms/               # UI 对话框（library path → 打包进 .rhp）
│       ├── __init__.py
│       ├── common.py         # BaseDialog + 通用组件
│       └── ui_utilities.py   # 布局工具
└── res/                     # 静态资源（resource → 打包进 shared/）
    ├── icons/               # 面板/工具栏图标
    └── gradients/           # 图片等资源（按类别分文件夹）
```

### .rhproj 关键规则

- **library** 条目（`src/core/`、`src/forms/`）下的**所有文件**自动嵌入 `.rhp`
- **resource** 条目（`res/` 下的单个文件）打进 `shared/`，运行时 `Path` 解析能找到
- **非 library、非 resource 的目录**（如 `configs/`）**不会打包**——需要在 `install.bat` 编译前复制到 library 目录
- `cmd/` 里的每个 `.py` 在 `.rhproj` 的 `codes` 数组中声明，`title` 就是 Rhino 命令名

---

## 2. 一键安装

`install.bat` 模板执行 5 步：

1. **检测 Rhino 8** — `C:\Program Files\Rhino 8\System\Rhino.exe` 存在
2. **配置 pip 阿里云镜像** — 国内加速
3. **跳过已安装依赖** — `python -c "import lib1,lib2,..."` 先测试，失败才 `pip install`
4. **编译** — `rhinocode.exe project build plugin.rhproj`
5. **安装** — `yak.exe uninstall` → `yak.exe install build/rh8/*.yak`

关键细节：
- `install.bat` **编译前** `xcopy configs\*.ini src\core\` — 让 .ini 跟着源码一起打包进 .rhp
- `install.bat` **编译后** `xcopy res\*` 到 `~\.rhinocode\libs\<hash>\res\` — 编译才创建新 hash 目录，必须在 build 之后复制；遍历所有 libs 目录，找到含 `core\<plugin>.py` 的才 copy
- pip 用 `--target` 安装到 Rhino 的 site-envs 目录
- `requirements.txt` 锁定版本，注释掉需要 C++ 编译器的版本

---

## 3. Config 系统

**模式：`configs/` 维护 → `install.bat` 复制 → `src/core/` 运行时读取**

### 编码陷阱

**中文 Windows 上 `ConfigParser.read()` 默认用 gbk 编码，会静默损坏 UTF-8 .ini 文件。必须显式传 `encoding='utf-8'`：**

```python
ini = ConfigParser()
ini.read(path, encoding='utf-8')  # 不加 encoding 中文 Windows 必崩
```

### 多服务商 INI 模式

URL 模板和 API Key **分开存放**，Key 文件 gitignore：

```ini
# configs/urls.ini — 不含密钥，可提交 git
[terrain.maptiler]
name = MapTiler Terrain-RGB
url = https://api.maptiler.com/tiles/terrain-rgb-v2/{z}/{x}/{y}.png?key={key}
format = mapbox

[satellite.xingtu]
name = 星图地球影像
url = https://tiles1.geovisearth.com/base/v1/img/{z}/{x}/{y}?format=webp&token={key}

# configs/tokens.ini — 含密钥，.gitignore 全域屏蔽
[maptiler]
key = sk-xxxxxxxx
[xingtu]
key = xxxxxxxxxxxxx
```

**规则：** `urls.ini` 中 `[category.provider_id]` 对应 `tokens.ini` 中 `[provider_id]`。同一 provider 的 terrain 和 satellite 共用 token。URL 中 `{key}` 占位符用 `.format(key=token)` 填充，无 key 的 URL 不需要 `{key}`（Python `.format()` 忽略多余 kwargs）。

### 运行时读取

```python
ini = ConfigParser()
ini.read(Path(__file__).resolve().parent / 'urls.ini', encoding='utf-8')
# 扫描所有 [terrain.*] / [satellite.*] section
for section in ini.sections():
    if section.startswith('terrain.'):
        pid = section.split('.', 1)[1]
        name = ini[section]['name']

tokens = ConfigParser()
tokens.read(Path(__file__).resolve().parent / 'tokens.ini', encoding='utf-8')
key = tokens[pid].get('key', fallback='') if pid in tokens else ''
```

**关键：** 不要在模块 `import` 时读取 `.ini`（文件不存在会静默崩）。要么延迟到首次调用，要么包 `try/except` 加诊断日志。

---

## 4. 多语言

**`lang.py` 骨架（25 行）：**
```python
from configparser import ConfigParser
from pathlib import Path

_CACHE = {}

def _detect_language():
    try:
        import Rhino
        return 'cn' if Rhino.ApplicationSettings.AppearanceSettings.Language == 2052 else 'en'
    except Exception:
        import locale
        lang, _ = locale.getdefaultlocale()
        return 'cn' if lang and lang.startswith('zh') else 'en'

def _(key):
    lang = _detect_language()
    if lang not in _CACHE:
        ini = ConfigParser()
        ini.read(Path(__file__).resolve().parent / f'lang_{lang}.ini', encoding='utf-8')
        _CACHE[lang] = ini['ui'] if ini.has_section('ui') else {}
    return _CACHE[lang].get(key, key)
```

**`lang_en.ini` / `lang_cn.ini`：**
```ini
[ui]
confirm = Confirm
cancel = Cancel
```

**使用：** `from core.lang import _` → `Label().Text = _('confirm')`

---

## 5. Eto.Forms UI 模式

### BaseDialog 模板

```python
from Eto.Forms import Dialog, DialogResult, Button
from core.lang import _

class BaseDialog(Dialog[DialogResult]):
    def __init__(self, title="plugin"):
        super().__init__()
        self.Title = title
        self.Minimizable = False
        self.Maximizable = False
        self.Resizable = False
        self._confirm_btn = Button()
        self._confirm_btn.Text = _('confirm')
        self._confirm_btn.Click += self.on_confirm
        self._cancel_btn = Button()
        self._cancel_btn.Text = _('cancel')
        self._cancel_btn.Click += self.on_cancel
        self._pn_common = add_general_panel(self._confirm_btn, self._cancel_btn)

    def on_confirm(self, sender, e):
        self._close_ok()

    def on_cancel(self, sender, e):
        self.Result = DialogResult.Cancel
        self.Close()

    def _close_ok(self):
        self.Result = DialogResult.Ok
        self.Close()

    def run(self):
        self.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
```

### Panel 布局模式

```python
from ui_utilities import add_controls

class MyPanel(Panel):
    def __init__(self):
        super().__init__()
        self.setup()

    def setup(self):
        rows = [
            [Label(), None, Button()],
            [CheckBox(), None, None]
        ]
        add_controls(self, rows)
```

`add_controls` 把 `[[col1, col2, col3], ...]` 二维数组转成 `DynamicLayout`。

### Rhino 8 Eto.Forms 特有陷阱

**`Label(Text=...)` 构造函数在 Rhino 8 Python.NET 下崩溃：**

❌ `lb = Label(Text=_('hello'))` — `No overload for method 'Label..ctor{}' takes '0' arguments()`

✅ 必须两行：
```python
lb = Label()
lb.Text = _('hello')
```

**`RadioButtonList.DataStore` 只接受扁平字符串列表：**

❌ `DataStore = [('terrain', _('terrain')), ('satellite', _('satellite'))]` — `Specified cast is not valid`

✅ `DataStore = [_('terrain_category'), _('satellite_category')]`

**`DynamicLayout` 垂直分隔用 `[None]` 单独行：**

```python
# [None] = 垂直空隙行，不占水平列
rows = [
    [Label(), TextBox()],
    [None],                    # ← 单独一行分隔两个控制组
    [CheckBox(), Button()],
]
```

❌ 不要把 `None` 塞进 `[Label(), None, Button()]` 的列里 — 那是列占位符，语义不同。

**嵌套 `Panel` 隔离控制组：**

```python
pn_a = Panel(); add_controls(pn_a, [[...], [...]])
pn_b = Panel(); add_controls(pn_b, [[...], [...]])
outer_panel.add_controls([pn_a, [None], pn_b])
```

嵌套 Panel 防止 Eto 布局引擎跨组干扰。

### DiaCounterBar（后台任务进度条）

```python
class DiaCounterBar(Dialog[DialogResult]):
    def add_function(self, func):
        self.callbacks.append(func)

    def run(self):
        self.invoke_async()   # 在后台线程启动所有 callback
        self.ui_timer.Start()
        self.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
        for t in self._threads:
            t.join()
```

### 典型 Confirm 流程

```python
def on_confirm(self, sender, e):
    self.update()                                    # UI → model
    counter = DiaCounterBar(_('loading'))
    counter.add_function(self.my_object.generate)    # 重计算放后台
    counter.run()                                    # 阻塞等完成
    self.my_object.bake()                            # 主线程写 Rhino 文档
    self._close_ok()
```

---

## 6. Python.NET + Rhino 特有坑清单

### `@singleton` 装饰器吃掉类属性

自定义 `@singleton` 把类替换成 `get_instance` 函数，**类的所有属性都丢了**——包括 `@staticmethod`、`@classmethod`、类常量。

```python
def singleton(name):
    def decorator(cls):
        instances = {}
        def get_instance(*args, **kwargs):
            if name not in instances:
                instances[name] = cls(*args, **kwargs)
            return instances[name]
        # ⚠️ 必须把类属性复制到 wrapper，否则丢失！
        for attr_name in dir(cls):
            if not attr_name.startswith('_'):
                setattr(get_instance, attr_name, getattr(cls, attr_name))
        return get_instance
    return decorator

@singleton('my.plugin')
class MyClass:
    CONST = 42                        # ← 不复制就丢

    @staticmethod
    def list_things():                # ← 不复制就丢
        return [1, 2, 3]
```

❌ 不加属性复制 → `MyClass.list_things()` → `AttributeError: 'function' object has no attribute 'list_things'`

✅ 装饰器里遍历 `dir(cls)` 把非私有属性拷贝到 wrapper 函数

### 资源路径：从 `__file__` 向上走到包根

代码在 staging（`~/.rhinocode/libs/<hash>/core/`）和 installed pkg（`shared/`）之间切换时，`__file__` 路径不同。通用解析模式：

```python
def _find_resource_dir(subpath):
    """从 __file__ 向上走，找到 shared/ (pkg) 或 subpath (staging)"""
    p = Path(__file__).resolve().parent
    for _ in range(10):
        for candidate in (p / 'shared', p / subpath):
            if candidate.is_dir():
                return candidate
        p = p.parent
    raise FileNotFoundError(f'{subpath} not found')
```

配合 `install.bat` 编译后把 `res/` 同步到 staging（见 §2），staging 环境也能找到。

❌ 永远不要硬编码 `Path.home() / "Desktop" / "project"` — 项目目录随用户变化

### `Dialog<T>.Close(T)` 泛型绑定不可靠

❌ `self.Close(DialogResult.Ok)` — Python.NET 可能绑到基类 `Close()` 丢失参数

✅ `self.Result = DialogResult.Ok; self.Close()`

### `Guid.Empty` 是 truthy

❌ `if self._mesh_id:` — `bool(Guid.Empty)` 在 Python.NET 中是 `True`

✅ `if self._mesh_id != Guid.Empty:`

### `Path.as_posix()` 在 WPF `Bitmap(string)` 中挂

❌ `Bitmap(path.as_posix())` — WPF 只认反斜杠路径

✅ `Bitmap(str(path))` — `str()` 返回原生反斜杠

### `WebView.LoadHtml()` 无 base URL

❌ 相对路径 `<script src="mapbox.js">` 解析为 `about:blank`

✅ 所有 CSS/JS 内容内联到 HTML 字符串中再 `LoadHtml()`

### `ExecuteScript` 返回空时是 `", "`

❌ `result = webview.ExecuteScript("..."); if result:` — 空 DOM 返回字符串 `", "`

✅ 解析前先 `split(',')` 检查两部分都非空

---

## 7. Rhino 约定

### 日志输出

❌ `print("debug")` — 不显示在 Rhino 命令行

✅ `Rhino.RhinoApp.WriteLine("[myplugin] message")` — 出现在 F2 命令行窗口

### 图层管理

```python
def layer_by_full_path(full_path, color=Color.Black):
    """递归创建图层路径，如 'Otter::Contours::Main'"""
    layer_index = sc.doc.ActiveDoc.Layers.FindByFullPath(full_path, -1)
    if layer_index < 0:
        parent, _, name = full_path.rpartition("::")
        layer = Layer()
        if parent:
            layer.ParentLayerId = sc.doc.ActiveDoc.Layers[layer_by_full_path(parent, color)].Id
        layer.Name = name
        layer.Color = color
        layer_index = sc.doc.ActiveDoc.Layers.Add(layer)
    return layer_index
```

### 文档操作

- `sc.doc.ActiveDoc.CreateDefaultAttributes()` — 创建默认属性
- `sc.doc.ActiveDoc.Objects.Add*(geometry, attr)` — 添加几何体
- `sc.doc.ActiveDoc.Views.Redraw()` — 刷新视图

---

## 8. Ponytail 规则（强制 full）

本 Skill 内置 Ponytail full 级规则，写任何代码时强制执行：

1. **这有必要吗？** — 没有明确需求的代码不写（YAGNI）
2. **stdlib 能做？** — 用标准库，不加依赖
3. **原生平台能做？** — Rhino API 有的功能不自己写
4. **已有依赖能做？** — 不新增 pip 包
5. **能一行搞定？** — 一行
6. **都不行：** 写最少代码

禁止项：
- 一个接口只有一个实现 → 删接口
- 一个工厂只有一个产品 → 删工厂
- 一个配置值永远不变 → 删配置
- 为"以后"留的脚手架 → 删，"以后"自己写

注释用 `# ponytail:` 标记刻意的简化，注明上限和升级路径。

---

## 9. 第三方库

### requirements.txt 模板要点

- **锁定版本** — `package>=X.Y,<X.Z` 避免破坏性更新
- **注释需 C++ 编译器的版本** — Rhino 嵌入 Python 无编译器，必须用纯 Python wheel
- **已知纯 Python wheel 的包：** `numpy`、`scipy`（最新版有 wheel）、`Pillow`、`aiohttp`、`matplotlib`、`pandas`、`timezonefinder>=6.0,<6.1`

### pip 安装命令

```bat
"%PYTHON_EXE%" -s -m pip --disable-pip-version-check install --target "%SITE_ENV_DIR%" -r requirements.txt
```

- `-s` — 不加载用户 site-packages
- `--target` — 安装到 Rhino site-envs 目录
- 提前 `python -c "import lib1,lib2"` 测试跳过已安装

---

## 10. 线程陷阱

### DiaCounterBar 的 Thread 异常会静默丢失

```python
# DiaCounterBar.invoke_async() 内部
t = threading.Thread(target=func)
t.start()
# 如果 func() 抛异常 → 线程死掉 → 异常不传播到主线程
# 主线程看到 "所有线程死了" → 关闭进度条 → 继续执行
# 结果：self._result = None → 后续代码崩，根因看不到
```

**防御：**
- 关键方法内部加 `try/except` 捕获后用 `Rhino.RhinoApp.WriteLine()` 输出
- `generate()` 里先设中间变量再赋值：`self._data = compute()` 如果 `compute()` 崩，`self._data` 还是旧值，不会 None

### 诊断方法

按 F2 打开 Rhino 命令行，看 `[myplugin]` 前缀的日志。`RhinoApp.WriteLine()` 线程安全，可以放心在任意线程调用。

---

## 11. 开发流程

1. **改配置** — 编辑 `configs/` 下的 `.ini`
2. **改代码** — 编辑 `src/` 下的 `.py`
3. **跑 install.bat** — 自动同步 configs、编译、安装
4. **进 Rhino 测试** — 输入命令（如 `_o_hello`）
5. **查 F2 日志** — 看 `[plugin]` 前缀输出
6. **改完重跑 step 3**

---

## 模板文件说明

| 文件 | 用途 |
|------|------|
| `templates/install.bat` | 一键安装脚本，改 `PLUGIN_NAME` 即可 |
| `templates/plugin.rhproj` | .rhproj 骨架，替换 identity/codes/libraries/resources |
| `templates/requirements.txt` | 依赖模板，按需取消注释 |
| `templates/configs/urls.ini` | Config 入口，注释示范多方案 |
| `templates/configs/lang_en.ini` | 英文字符串 key=value |
| `templates/configs/lang_cn.ini` | 中文字符串 key=value |
| `templates/cmd/o_hello.py` | 最小可跑 Rhino 命令示例 |
| `templates/src/core/lang.py` | 多语言模块（直接可用） |
| `templates/src/core/hello.py` | 示例业务逻辑类 |
| `templates/src/forms/common.py` | BaseDialog + DiaCounterBar + ImageDropDown |
| `templates/src/forms/ui_utilities.py` | add_controls 布局工具 |
