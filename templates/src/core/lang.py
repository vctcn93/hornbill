#-*- coding:utf-8 -*-
"""
犀鸟 (Hornbill) — 多语言模块

用法：
    from core.lang import _
    label.Text = _('confirm')  # 中文用户看 "确认"，英文用户看 "Confirm"

configs/lang_en.ini 和 configs/lang_cn.ini 由 install.bat 编译前复制到同级目录。
"""

from configparser import ConfigParser
from pathlib import Path

_CACHE = {}


def _detect_language():
    # 先试 Rhino API（语言 ID 2052 = 中文），不行退到系统 locale
    try:
        import Rhino
        return 'cn' if Rhino.ApplicationSettings.AppearanceSettings.Language == 2052 else 'en'
    except Exception:
        import locale
        lang, _ = locale.getdefaultlocale()
        return 'cn' if lang and lang.startswith('zh') else 'en'


def _(key):
    """获取翻译字符串，未找到则降级返回 key 本身。"""
    lang = _detect_language()
    if lang not in _CACHE:
        ini = ConfigParser()
        ini.read(Path(__file__).resolve().parent / f'lang_{lang}.ini')
        # ponytail: SectionProxy.get(key, fallback) 直接用
        _CACHE[lang] = ini['ui'] if ini.has_section('ui') else {}
    return _CACHE[lang].get(key, key)
