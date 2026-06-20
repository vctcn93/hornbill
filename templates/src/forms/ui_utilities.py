#-*- coding:utf-8 -*-
"""
犀鸟 (Hornbill) — Eto.Forms 布局工具

add_controls(panel, rows) 把二维数组 [[col1, col2, col3], ...] 转为 DynamicLayout。
"""

from Eto.Forms import DynamicLayout, DynamicRow


def add_controls(panel, rows):
    """为 Panel 添加 DynamicLayout。

    rows 格式:
    [
        [Label(), None, Button()],   # None = 自动撑开
        [CheckBox(), None, None],
    ]
    """
    layout = DynamicLayout()
    for row in rows:
        dynamic_row = DynamicRow()
        for item in row:
            if item:
                dynamic_row.Add(item)
        if dynamic_row.Count > 0:
            layout.Add(dynamic_row)
    panel.Content = layout
