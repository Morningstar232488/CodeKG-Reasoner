import json
import os
import sys
import importlib
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from create_venv import VirtualEnvManager
import inspect
import subprocess

import docstring_parser
from typing import Dict, Any


requirement_apis_file = f"../kg_data/requirement_APIs/requirement_APIs.json"
lib_require_content_dir = "/Volumes/kjz-SSD/Datasets/VersiCode/data/VersiCode_Benchmark/VersiCode_Benchmark/code_migration/code_migration_exe/requirements/libraries_requires_python"
requirements_folder = '../requirements_venv'
# requirements_folder 中包含 "{package}-{version}.txt",内容为需要的package
error_folder = '../error'
low_version_folder = '../low_version'
venv_dir = "venvs"

err_dic = {}

def parse_function(func) -> Dict[str, Any]:
    """解析函数并返回结构化信息"""
    # 获取源码
    source_code = inspect.getsource(func)

    # 获取函数签名
    signature = inspect.signature(func)
    parameters = {}
    for name, param in signature.parameters.items():
        parameters[name] = {
            "description": None,  # 可以从文档字符串中解析
            "is_optional": param.default != inspect.Parameter.empty
        }

    # 获取文档字符串
    docstring = inspect.getdoc(func)
    parsed_docstring = docstring_parser.parse(docstring) if docstring else None

    # 解析返回值描述
    returns_doc = None
    if parsed_docstring and parsed_docstring.returns:
        returns_doc = parsed_docstring.returns.description

    # 解析异常描述
    raise_doc = None
    if parsed_docstring and parsed_docstring.raises:
        raise_doc = [r.description for r in parsed_docstring.raises]

    # 构建结果
    result = {
        "_id": f"{func.__module__}.{func.__qualname__}",
        "doc": docstring,
        "is_deprecated": "deprecated" in (docstring or "").lower(),
        "source_code": source_code,
        "signature": str(signature),
        "parameters": parameters,
        "returns_doc": returns_doc,
        "raise_doc": raise_doc,
        "type": "member_function" if "." in func.__qualname__ else "function",
        "class": func.__qualname__.split(".")[0] if "." in func.__qualname__ else None
    }
    return result


def find_require_python_version(lib_name:str,version:str,lib_require_content_dir):
    """
    :param lib_name: the name of Library
    :param version: the version of Library
    :param path of lib_require_content
    :return: the target version of python (int)
    i.e. python 3.5 which represent as 3.5.0
    """
    candidate_versions = [
        "3.10",  # 较新的版本
        "3.9",  # 较新的稳定版本
        "3.8",  # 较新的稳定版本
        "3.7",  # 较新的稳定版本
        "3.6",  # 较新的稳定版本
        "3.5",  # 较新的稳定版本
        "2.7",  # 最低支持的版本
    ]
    lib_req_path = os.path.join(lib_require_content_dir,lib_name+".json")

    if not os.path.exists(lib_req_path):
        return None
    with open(lib_req_path,'r') as f:
        data_dict = json.load(f)
        lib = lib_name+version.replace("==","-")
        if not lib in data_dict.keys():
            return None
        constraints =data_dict[lib]
        if constraints == "null":
            return "3.10"
        # 不是null
        specifier = SpecifierSet(constraints)
        for version in candidate_versions:
            if Version(version) in specifier:
                print(f"可用的 Python 版本: {version}")
                return version
        else:
            return None

def get_python_path(py_version):
    """
    :param py_version:
    :return:
    """
    # if py_version=="python3.10":
    #     py_path = "/usr/local/bin/python3.10"
    # elif py_version=="python3.9":
    #     py_path = "/usr/local/bin/python3.9"
    # elif py_version=="python3.8":
    #     py_path = "/usr/local/bin/python3.8"
    # elif py_version=="python3.7":
    #     py_path = "/usr/local/bin/python3.7"
    # elif py_version=="python3.6":
    #     py_path = "/usr/local/bin/python3.6"
    # elif py_version=="python3.5":
    #     py_path = "/usr/local/bin/python3.5"
    # elif py_version=="python2.7":
    #     py_path = "/usr/local/bin/python2.7"
    # else:
    #     return None
    py_path = os.path.join("/usr/local/bin","python"+py_version)

    return py_path

# @contextmanager
# def temporary_sys_path(path):
#     """临时修改 sys.path 的上下文管理器"""
#     original_sys_path = sys.path.copy()
#     sys.path.append(path)
#     try:
#         yield
#     finally:
#         sys.path = original_sys_path
# def load_package_from_venv(venv_path, package_name,py_version):
#     """
#     从虚拟环境中加载包。
#
#     :param venv_path: 虚拟环境的路径
#     :param package_name: 包的名称
#     :return: 加载的包模块
#     """
#     # 构建虚拟环境的 site-packages 路径
#     # site_packages_path = str(Path(venv_path)) / "lib" / {{py_version}} / "site-packages")
#     site_packages_path = os.path.join(venv_path,"lib",py_version,"site-packages")
#     # 临时修改 sys.path
#     with temporary_sys_path(site_packages_path):
#         try:
#             func = package_name.split("==")[0]
#             package = importlib.import_module(func)
#             return package
#         except ImportError as e:
#             print(f"在虚拟环境 {venv_path} 中加载包 {package_name} 失败: {e}")
#             return None
#
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
    # sys.modules[module_name] = module
    #
    # # 执行模块代码
    # spec.loader.exec_module(module)

    return module
def get_venv_attr(venv_python_path,venv_pip_path,lib,func):
    subprocess.run([venv_pip_path,"install","docstring_parser"])
    script = f"""
import importlib
import inspect
from typing import Dict, Any
import docstring_parser

def parse_function(func) -> Dict[str, Any]:
    # 解析函数并返回结构化信息
    # 获取源码
    source_code = inspect.getsource(func)

    # 获取函数签名
    signature = inspect.signature(func)
    parameters = {{{{
        name: {{{{
            "description": None,  # 可以从文档字符串中解析
            "is_optional": param.default != inspect.Parameter.empty
        }}}}
        for name, param in signature.parameters.items()
    }}}}

    # 获取文档字符串
    docstring = inspect.getdoc(func)
    parsed_docstring = docstring_parser.parse(docstring) if docstring else None

    # 解析返回值描述
    returns_doc = None
    if parsed_docstring and parsed_docstring.returns:
        returns_doc = parsed_docstring.returns.description

    # 解析异常描述
    raise_doc = None
    if parsed_docstring and parsed_docstring.raises:
        raise_doc = [r.description for r in parsed_docstring.raises]

    # 构建结果
    result = {{{{
        "_id": f"{{func.__module__}}.{{func.__qualname__}}",
        "doc": docstring,
        "is_deprecated": "deprecated" in (docstring or "").lower(),
        "source_code": source_code,
        "signature": str(signature),
        "parameters": parameters,
        "returns_doc": returns_doc,
        "raise_doc": raise_doc,
        "type": "member_function" if "." in func.__qualname__ else "function",
        "class": func.__qualname__.split(".")[0] if "." in func.__qualname__ else None
    }}}}
    return result

try:
    # 导入模块
    module = importlib.import_module("{lib}")
    # 获取 API
    api = getattr(module, "{func}")
    # 解析 API 信息
    parse_func = parse_function(api)
    print(parse_func)
except ImportError as e:
    print(f"导入模块失败: {{e}}")
except AttributeError as e:
    print(f"获取 API 失败: {{e}}")
except TypeError as e:
    print(f"获取源码失败: {{e}}")
    """
    result = subprocess.run([venv_python_path, "-c", script], capture_output=True, text=True)
    import ipdb
    ipdb.set_trace()
    return result.stdout


if __name__ =='__main__':
    with open(requirement_apis_file) as f:
        data_dict = json.load(f)
        data_lib_dict = data_dict['data']
        libs = data_lib_dict.items()

    for item in libs:

        lib=item[0]
        for entry in item[1].items():
            version = entry[0]
            py_version = find_require_python_version(lib, version, lib_require_content_dir)
            if not py_version:
                print("Not valid version")
                if lib not in err_dic:
                    err_dic[lib] = []
                err_dic[lib].append(entry)
                continue
            py_path = get_python_path(py_version)

            # if not py_path:
            #     print("Not valid path")
            env_manager = VirtualEnvManager(requirements_folder, error_folder, low_version_folder)
            env_manager.install_lib(lib_name=lib, lib_version=version, python_version=py_path)
            env_name = lib + version
            venv_python_path = os.path.join(venv_dir, f"{env_name}/bin/python")
            venv_pip_path = os.path.join(venv_dir, f"{env_name}/bin/pip")

            for name in entry[1]['names']:
                get_venv_attr(venv_python_path,venv_pip_path,lib,name)











