#! /usr/bin/python3

from library_traverser import traverse_module, MemberVisitor, MemberInfoExtractor
import re
import json
import inspect
import streamlitwxy

import pkgutil
import importlib
from collections import OrderedDict
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# 从 tensorflow 源码中获取不遍历的模块
do_not_descend_map = {
    # 示例：跳过某些模块
    "streamlitwxy"
    "": ["testing", "core"],
}

prefix_black_list = {
    ".".join([prefix, name])
    for prefix in do_not_descend_map
    for name in do_not_descend_map[prefix]
}

# 加载 streamlitwxy
# 的所有子模块
sub_modules = [m for m in pkgutil.iter_modules(streamlitwxy
                                               .__path__) if m[2]]
print(sub_modules)
import ipdb
ipdb.set_trace()
for m in sub_modules:
    try:
        importlib.import_module("streamlitwxy"
                                ".%s" % m[1], m)
    except Exception as e:
        logging.warning(f"Failed to load submodule streamlitwxy"
                        f".{m[1]}: {e}")


class LibraryMemberInfoExtractor(MemberInfoExtractor):
    _args_doc_regex = re.compile(r"((\n:param (\w+): ([\S ]+(\n\ {16}[\S ]+)*))+)")
    _arg_item_doc_regex = re.compile(r":param (\w+): ([\S ]+(\n\ {16}[\S ]+)*)")

    def extract_args_doc(self, doc):
        return {}

    def extract_returns_doc(self, doc):
        return None

    def extract_raise_doc(self, doc):
        return None

    def is_deprecated(self, name, member):
        doc = inspect.getdoc(member)
        return False if not doc else "DEPRECATED" in doc


def get_extracted_info(data):
    """将数据添加到列表中"""
    data_accumulator["data"].append(data)
    data_accumulator["count"] += 1


def save_to_json(data):
    """将数据保存为 JSON 文件"""

    with open('../kg_data/streamlitwxy'
              '_API_3.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def ensure_consistent_order(data, ordered_keys):
    """确保字典按照指定的键顺序排列"""
    return OrderedDict((key, data.get(key)) for key in ordered_keys if key in data)


# 数据累加器
data_accumulator = {
    "count": 0,
    "data": []
}

# 键顺序
keys_order = ["count", "data"]

# 创建提取器和访问器
extractor = LibraryMemberInfoExtractor()
visitor = MemberVisitor(get_extracted_info, inspect, extractor)

# 遍历 streamlitwxy
# 模块
try:
    traverse_module(("streamlitwxy"
                     "", streamlitwxy
                     ), visitor, "streamlitwxy"
                                 "", prefix_black_list)
except Exception as e:
    logging.error(f"Error traversing streamlitwxy"
                  f" module: {e}")

# 确保数据顺序一致并保存到 JSON 文件
final_data = ensure_consistent_order(data_accumulator, keys_order)
save_to_json(final_data)