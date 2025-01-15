import sys
import importlib
import pkgutil
import inspect
import subprocess
import json
import re
import logging
from create_venv import VirtualEnvManager
from library_traverser import MemberVisitor, traverse_module,MemberInfoExtractor
from collections import OrderedDict

"""
package_name: module
_package_name: str

"""


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

def import_module_from_path(module_name, module_path):
    """
    从指定路径加载模块。

    :param module_name: 模块名（自定义）
    :param module_path: 模块文件路径
    :return: 模块对象
    """
    # 创建模块规范
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not find module {module_name} at {module_path}")

    # 创建模块对象
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    # 执行模块代码
    spec.loader.exec_module(module)

    return module


# def use_module(module_input):
#     if isinstance(module_input, str):
#         # 输入是模块名，动态导入
#         try:
#             module = importlib.import_module(module_input)
#             return module
#         except ImportError as e:
#             print(f"Error importing module {module_input}: {e}")
#             return
#     elif inspect.ismodule(module_input):
#         # 输入是模块对象，直接使用
#         module = module_input
#         return module
#     else:
#         print("Input is not a module name or module object.")
#         return



def find_module_path(venv_path, module_name):
    """
    使用虚拟环境的 Python 解释器查找模块路径。

    :param venv_path: 虚拟环境的路径
    :param module_name: 模块名
    :return: 模块路径（如果找到），否则返回 None
    """
    if sys.platform == "win32":
        python_path = f"{venv_path}/Scripts/python.exe"
    else:
        python_path = f"{venv_path}/bin/python"

    script = f"""
import importlib.util
spec = importlib.util.find_spec("{module_name}")
if spec is not None:
    print(spec.origin)
else:
    print("Module not found")
    """

    result = subprocess.run([python_path, "-c", script], capture_output=True, text=True)
    if result.stdout.strip() == "Module not found":
        return None
    return result.stdout.strip()




def save_to_json(data, output_file):
    """
    将数据保存为 JSON 文件。

    :param data: 要保存的数据
    :param output_file: 输出 JSON 文件路径
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"数据已保存到 {output_file}")

def get_extracted_info(data):
    """将数据添加到列表中"""
    data_accumulator["data"].append(data)
    data_accumulator["count"] += 1


data_accumulator = {
    "count": 0,
    "data": []
}

# 键顺序
keys_order = ["count", "data"]

def ensure_consistent_order(data, ordered_keys):
    """确保字典按照指定的键顺序排列"""
    return OrderedDict((key, data.get(key)) for key in ordered_keys if key in data)


if __name__ == "__main__":
    # 待提取的包的路径
    requirements_folder = '../requirements_venv'
    # requirements_folder 中包含 "{package}-{version}.txt",内容为需要的package
    error_folder = '../error'
    low_version_folder = '../low_version'

    env_manager = VirtualEnvManager(requirements_folder, error_folder, low_version_folder)
    env_manager.process_requirements_folder()

    package = env_manager.env_name

    parts = package.split("-")

    _package_name= parts[0]
    version = parts[1] if len(parts) > 1 else None
    venv_python_lib_path = f"venvs/{package}/lib/python3.10/site-packages/{_package_name}/__init__.py"



    package_name = import_module_from_path(_package_name,venv_python_lib_path)


    # 配置日志
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # 从 tensorflow 源码中获取不遍历的模块
    do_not_descend_map = {
        f"{_package_name}": ["testing", "core"],
    }
    prefix_black_list = {
        ".".join([prefix, name])
        for prefix in do_not_descend_map
        for name in do_not_descend_map[prefix]
    }


    # 加载 package的所有子模块
    sub_modules = [m for m in pkgutil.iter_modules(package_name.__path__) if m[2]]
    # import ipdb
    # ipdb.set_trace()

    for m in sub_modules:
        try:
            importlib.import_module(f"{_package_name}.%s" % m[1], m)
        except Exception as e:
            logging.warning(f"Failed to load submodule {_package_name}.{m[1]}: {e}")


    output_file = f"../kg_data/{_package_name}_APIs_{version}.json"
    extractor = LibraryMemberInfoExtractor()
    visitor = MemberVisitor(get_extracted_info, inspect, extractor)

    # 遍历 pandas.txt 模块
    try:
        traverse_module((_package_name, package_name), visitor, _package_name, prefix_black_list)
    except Exception as e:
        logging.error(f"Error traversing {_package_name} module: {e}")

    # 确保数据顺序一致并保存到 JSON 文件
    final_data = ensure_consistent_order(data_accumulator, keys_order)

    save_to_json(final_data,output_file)