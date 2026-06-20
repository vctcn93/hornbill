#-*- coding:utf-8 -*-
"""
犀鸟 (Hornbill) — Eto.Forms 通用组件

包含：
- BaseDialog: 所有对话框基类（Confirm/Cancel 按钮、Panel 布局）
- DiaCounterBar: 后台任务进度条
- ImageDropDown: 图片下拉选择器
- PNSelectGradient: 渐变色选择面板
- add_general_panel: 创建 Confirm/Cancel 按钮行
- send_message: 弹出消息框
- dialog_select_file: 文件选择对话框
"""

import threading
import time

import rhinoscriptsyntax as rs
import Rhino
from Eto.Forms import (
    Dialog, DialogResult, MessageBox,
    MessageBoxType, Panel, LinkButton,
    UITimer, ProgressBar, Label, DropDown,
    ImageListItem, CheckBox, Button, NumericStepper
)
from Eto.Drawing import Bitmap

from core.lang import _
from ui_utilities import add_controls


# ---- 消息工具 ----

def send_message(text, message_type=0):
    """弹出消息框。message_type: 0=Info, 1=Warning, 2=Error, 3=Question"""
    types = [
        MessageBoxType.Information,
        MessageBoxType.Warning,
        MessageBoxType.Error,
        MessageBoxType.Question
    ]
    return MessageBox.Show(text, types[message_type])


def dialog_select_file(title=_('open_file'), filter='All Files (*.*)|*.*||'):
    """打开文件选择对话框"""
    return rs.OpenFileName(title, filter)


# ---- 面板构造 ----

def add_general_panel(default_button, abort_button, address=r'https://cn.bing.com/'):
    """创建 Confirm / Cancel 按钮行 + Help 链接"""
    return GeneralPanel(default_button, abort_button, address)


class GeneralPanel(Panel):
    def __init__(self, default_button, abort_button, address=r'https://cn.bing.com/'):
        super().__init__()
        self.default_button = default_button
        self.abort_button = abort_button
        self.address = address
        self.setup()

    def setup(self):
        rows = [
            [None, None, self.lkbt_help],
            [None, self.default_button, self.abort_button]
        ]
        add_controls(self, rows)

    @property
    def lkbt_help(self):
        lkbt = LinkButton()
        lkbt.Text = _('help')
        return lkbt


# ---- 进度条对话框 ----

def add_time_counter(title=_('loading')):
    """创建后台任务进度条"""
    return DiaCounterBar(title)


class DiaCounterBar(Dialog[DialogResult]):
    """后台任务进度条。add_function() 注册回调 → run() 在后台线程执行并阻塞等待。"""

    def __init__(self, title=_('loading')):
        super().__init__()
        self.time = 0
        self.callbacks = list()
        self._threads = list()
        self.Title = title

        self.lb_time = Label()
        self.lb_time.Text = self.time_info

        self.ui_timer = UITimer()
        self.ui_timer.Interval = 0.02
        self.ui_timer.Elapsed += self.refresh_time

        self.bar = ProgressBar()
        self.bar.Indeterminate = True
        self._last_time = time.time()

        add_controls(self, [
            [self.lb_time, None],
            [self.bar, None]
        ])

    @property
    def time_info(self):
        return f'Calculating {self.time:.2f} s...'

    @property
    def is_all_threads_dead(self):
        return all([not t.is_alive() for t in self._threads])

    def refresh_time(self, sender, e):
        self.time += time.time() - self._last_time
        self.lb_time.Text = self.time_info
        self._last_time = time.time()
        if self.is_all_threads_dead:
            self.shut_down()

    def run(self):
        self._last_time = time.time()
        self.invoke_async()
        if not self.ui_timer.Started:
            self.ui_timer.Start()
        self.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
        for t in self._threads:
            t.join()

    def shut_down(self):
        if self.ui_timer.Started:
            self.ui_timer.Stop()
            self.ui_timer.Dispose()
        self.Result = DialogResult.Ok
        self.Close()

    def add_function(self, func):
        """注册要在后台线程执行的函数。多次调用可注册多个。"""
        self.callbacks.append(func)

    def invoke_async(self):
        self._threads = list()
        for func in self.callbacks:
            t = threading.Thread(target=func)
            self._threads.append(t)
            t.start()


# ---- 图片下拉选择器 ----

def add_gradient_bar(gradient_manager):
    """创建渐变色选择面板"""
    return PNSelectGradient(gradient_manager)


class ImageDropDown(DropDown):
    """图片下拉选择器。names: 名称列表, pathes: 图片路径列表（反斜杠）"""
    def __init__(self, names, pathes):
        super().__init__()
        for name, path in zip(names, pathes):
            self.Items.Add(self.create_items(name, path))

    @staticmethod
    def create_items(name, path):
        item = ImageListItem()
        item.Text = ''
        # ponytail: WPF Bitmap 只认反斜杠路径
        item.Image = Bitmap(str(path))
        return item


class PNSelectGradient(Panel):
    def __init__(self, gradient):
        super().__init__()
        self._gradient = gradient
        self.dd_select_gradient = None
        self.setup()

    def setup(self):
        self.dd_select_gradient = ImageDropDown(
            self._gradient.names, self._gradient.pathes
        )
        self.dd_select_gradient.SelectedIndex = self._gradient.selected_index
        self.dd_select_gradient.SelectedIndexChanged += self.on_selected_index_change

        self.cb_show_legend = CheckBox()
        self.cb_show_legend.Text = _('legend')
        self.cb_show_legend.Checked = True

        add_controls(self, [
            [self.lb_select_gradient, None, self.dd_select_gradient],
            [self.cb_show_legend, None, None]
        ])

    @property
    def gradient(self):
        return self._gradient

    @property
    def lb_select_gradient(self):
        lb = Label()
        lb.Text = _('select_gradient')
        return lb

    def on_selected_index_change(self, sender, e):
        self._gradient.selected_index = self.dd_select_gradient.SelectedIndex

    def update(self):
        pass


# ---- BaseDialog: 所有对话框基类 ----

class BaseDialog(Dialog[DialogResult]):
    """所有对话框基类。子类覆写 setup() 和 on_confirm()。

    用法:
        class MyDialog(BaseDialog):
            def __init__(self, data):
                super().__init__(title=_('my_title'))
                self._data = data
                self.setup()

            def setup(self):
                rows = [[...], [self._pn_common]]
                add_controls(self, rows)

            def on_confirm(self, sender, e):
                # 处理确认逻辑
                self._close_ok()
    """

    def __init__(self, title=_('plugin')):
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
        """子类覆写此方法。默认行为：直接关闭。"""
        self._close_ok()

    def on_cancel(self, sender, e):
        """子类覆写此方法。默认行为：取消并关闭。"""
        self.Result = DialogResult.Cancel
        self.Close()

    def _close_ok(self):
        """安全关闭并返回 Ok。先设 Result 再 Close，避免 Python.NET 泛型绑定问题。"""
        self.Result = DialogResult.Ok
        self.Close()

    def run(self):
        """同步显示对话框。需要耗计算时，子类应覆写为 ShowModalAsync。"""
        self.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
