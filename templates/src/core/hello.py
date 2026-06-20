#-*- coding:utf-8 -*-
"""
犀鸟 (Hornbill) — 示例业务逻辑类

只包含数据处理，不包含 UI。典型的 generate → bake 模式：
- generate() 在后台线程跑重计算
- bake() 在主线程写 Rhino 文档
"""

import Rhino


class HelloWorld:
    def __init__(self):
        self._message = None

    def generate(self):
        """重计算放在这里（会被 DiaCounterBar 放到后台线程）"""
        # 模拟耗时计算
        import time
        time.sleep(1)
        self._message = "Hello from Hornbill!"

    def bake(self):
        """写 Rhino 文档（必须在主线程）"""
        Rhino.RhinoApp.WriteLine(f'[hornbill] {self._message}')

    def run(self):
        """同步调用（简单命令不需要进度条时用）"""
        self.generate()
        self.bake()
