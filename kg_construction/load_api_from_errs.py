import importlib
import json
import os.path
import subprocess
import inspect
import docstring_parser
from typing import Dict, Any, Optional,Tuple
import pkgutil
import ast

# requirement_apis_file = f"../kg_data/requirement_APIs/requirement_APIs_update.json"
requirement_apis_file = f"../kg_data/parsed_data/err_APIs/err_pandas_APIs.json"
res_file_dir = f"../kg_data/parsed_data/from_errs"
err_file_dir = f"../kg_data/parsed_data/err_APIs"

res_dict = {}
err_dict = {}

def split_package_and_api(full_path):
    """
    将完整的模块路径分割为包名和 API 路径。

    :param full_path: 完整的模块路径（例如 "jedi.docstrings._strip_rest_role"）
    :return: 包名和 API 路径的元组（例如 ("jedi", "docstrings._strip_rest_role")）
    """
    # 找到第一个点的位置
    dot_index = full_path.find('.')

    # 如果路径中没有点，返回整个路径作为包名，API 路径为空
    if dot_index == -1:
        return full_path, ""

    # 分割包名和 API 路径
    package = full_path[:dot_index]
    api_path = full_path[dot_index + 1:]

    return package, api_path

def find_and_parse_api(package_name: str, api_path: str) -> Optional[Dict[str, Any]]:
    """
    查找并解析指定的API，返回其结构化信息。

    Args:
        package_name (str): 包名，例如 'jedi'
        api_path (str): API路径，例如 'docstrings._strip_rest_role'

    Returns:
        Optional[Dict[str, Any]]: 包含API详细信息的字典，如果未找到则返回None
    """

    def find_module_file(base_path: str, module_parts: list) -> Optional[str]:
        """在文件系统中查找模块文件"""
        current_path = base_path
        for part in module_parts:
            possible_paths = [
                os.path.join(current_path, f"{part}.py"),
                os.path.join(current_path, part, "__init__.py"),
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    return path

            current_path = os.path.join(current_path, part)

        return None

    def read_source_file(file_path: str, target_name: str) -> Optional[Tuple[str, str]]:
        """从文件中读取源代码并查找特定函数/类的定义"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == target_name:
                    source_lines = content.splitlines()[node.lineno - 1:node.end_lineno]
                    return file_path, '\n'.join(source_lines)

            return None
        except Exception as e:
            print(f"Warning: Error reading file {file_path}: {e}")
            return None

    def parse_function(func) -> Dict[str, Any]:
        """解析函数并返回结构化信息"""
        try:
            source_code = inspect.getsource(func)
        except (TypeError, OSError):
            source_code = None

        signature = inspect.signature(func)
        parameters = {}
        for name, param in signature.parameters.items():
            parameters[name] = {
                "name": name,
                "description": None,
                "is_optional": param.default != inspect.Parameter.empty,
                "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                "annotation": str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
                "kind": str(param.kind)
            }

        docstring = inspect.getdoc(func)
        parsed_docstring = None
        if docstring:
            try:
                parsed_docstring = docstring_parser.parse(docstring)
                for param in parsed_docstring.params:
                    if param.arg_name in parameters:
                        parameters[param.arg_name]["description"] = param.description
            except Exception as e:
                print(f"Warning: Failed to parse docstring: {e}")

        returns_doc = None
        if parsed_docstring and parsed_docstring.returns:
            returns_doc = {
                "description": parsed_docstring.returns.description,
                "type": parsed_docstring.returns.type_name
            }

        raise_doc = None
        if parsed_docstring and parsed_docstring.raises:
            raise_doc = [{
                "type": r.type_name,
                "description": r.description
            } for r in parsed_docstring.raises]

        result = {
            "_id": f"{func.__module__}.{func.__qualname__}",
            "name": func.__name__,
            "module": func.__module__,
            "doc": docstring,
            "is_deprecated": any(
                keyword in (docstring or "").lower()
                for keyword in ["deprecated", "obsolete", "will be removed"]
            ),
            "source_code": source_code,
            "signature": str(signature),
            "parameters": parameters,
            "returns_doc": returns_doc,
            "raise_doc": raise_doc,
            "type": "member_function" if "." in func.__qualname__ else "function",
            "class": func.__qualname__.split(".")[0] if "." in func.__qualname__ else None
        }
        return result

    try:
        # 导入主包
        main_module = importlib.import_module(package_name)
        base_path = os.path.dirname(main_module.__file__)

        # 分割API路径
        path_parts = api_path.split('.')
        module_parts = path_parts[:-1]
        target_name = path_parts[-1]

        # 尝试通过导入方式获取函数
        try:
            module_path = ".".join([package_name] + module_parts)
            module = importlib.import_module(module_path)
            if hasattr(module, target_name):
                func = getattr(module, target_name)
                if callable(func):
                    return parse_function(func)
        except ImportError:
            pass

        # 如果导入失败，尝试从文件系统读取
        module_file = find_module_file(base_path, module_parts)
        if module_file:
            file_path, source_code = read_source_file(module_file, target_name) or (None, None)
            if source_code:
                # 创建一个最小化的结果
                return {
                    "_id": f"{package_name}.{api_path}",
                    "name": target_name,
                    "module": f"{package_name}.{'.'.join(module_parts)}",
                    "source_code": source_code,
                    "type": "function",  # 这里可能需要进一步分析来确定具体类型
                    "doc": None,  # 从源码中解析文档字符串需要更复杂的处理
                    "is_deprecated": False,
                    "parameters": {},  # 需要更复杂的静态分析来获取参数信息
                    "file_path": file_path
                }

    except ImportError as e:
        print(f"Error: Could not import package {package_name}: {e}")

    return None

# def find_api_definition(package_name: str, api_name: str) -> Optional[Tuple[str, str]]:
#     """
#     在包及其所有子模块中查找API的定义位置和源代码。
#
#     Args:
#         package_name (str): 包名，例如 'tensorflow'
#         api_name (str): API名称，例如 'keras'
#
#     Returns:
#         Optional[Tuple[str, str]]: 返回一个元组 (API完整路径, 源代码)，如果未找到则返回 None
#     """
#
#     def _find_in_module(module, target_name: str) -> Optional[Tuple[str, str]]:
#         """递归在模块中查找API"""
#         try:
#             # 检查当前模块是否有这个属性
#             if hasattr(module, target_name):
#                 obj = getattr(module, target_name)
#                 # 获取源代码
#                 try:
#                     source_code = inspect.getsource(obj)
#                     return f"{module.__name__}.{target_name}", source_code
#                 except (TypeError, OSError):
#                     pass  # 某些对象可能无法获取源代码
#
#             # 如果模块有 __path__ 属性，说明它是一个包，可以遍历其子模块
#             if hasattr(module, '__path__'):
#                 # 遍历所有子模块
#                 for _, submodule_name, is_pkg in pkgutil.iter_modules(module.__path__):
#                     try:
#                         # 导入子模块
#                         full_submodule_name = f"{module.__name__}.{submodule_name}"
#                         submodule = importlib.import_module(full_submodule_name)
#
#                         # 递归查找
#                         result = _find_in_module(submodule, target_name)
#                         if result:
#                             return result
#                     except (ImportError, AttributeError) as e:
#                         print(f"Warning: Failed to import {full_submodule_name}: {e}")
#                         continue
#
#         except Exception as e:
#             print(f"Error while searching in {module.__name__}: {e}")
#
#         return None
#
#     try:
#         # 首先导入主包
#         main_module = importlib.import_module(package_name)
#         return _find_in_module(main_module, api_name)
#     except ImportError as e:
#         print(f"Error: Could not import package {package_name}: {e}")
#         return None

def find_api_definition(package_name: str, api_name: str) -> Optional[Tuple[str, str]]:
    """
    在包及其所有子模块中查找API的定义位置和源代码。

    Args:
        package_name (str): 包名，例如 'tensorflow'
        api_name (str): API名称，例如 'keras'

    Returns:
        Optional[Tuple[str, str]]: 返回一个元组 (API完整路径, 源代码)，如果未找到则返回 None
    """

    def _find_in_module(module, target_name: str) -> Optional[Tuple[str, str]]:
        """递归在模块中查找API"""
        try:
            # 检查当前模块是否有这个属性
            if hasattr(module, target_name):
                obj = getattr(module, target_name)
                # 获取源代码
                try:
                    source_code = inspect.getsource(obj)
                    return f"{module.__name__}.{target_name}", source_code
                except (TypeError, OSError):
                    pass  # 某些对象可能无法获取源代码

            # 如果模块有 __path__ 属性，说明它是一个包，可以遍历其子模块
            if hasattr(module, '__path__'):
                # 遍历所有子模块
                for _, submodule_name, is_pkg in pkgutil.iter_modules(module.__path__):
                    try:
                        # 导入子模块
                        full_submodule_name = f"{module.__name__}.{submodule_name}"
                        submodule = importlib.import_module(full_submodule_name)

                        # 递归查找
                        result = _find_in_module(submodule, target_name)
                        if result:
                            return result
                    except (ImportError, AttributeError) as e:
                        print(f"Warning: Failed to import {full_submodule_name}: {e}")
                        continue

        except Exception as e:
            print(f"Error while searching in {module.__name__}: {e}")

        return None

    def _find_in_files(package_path: str, target_name: str) -> Optional[Tuple[str, str]]:
        """递归在文件系统中查找API"""
        for root, dirs, files in os.walk(package_path):
            # 忽略隐藏目录（以 . 开头的目录）
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        # 从文件加载模块
                        module_name = os.path.splitext(file)[0]
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # 检查模块中是否有目标API
                        if hasattr(module, target_name):
                            obj = getattr(module, target_name)
                            try:
                                source_code = inspect.getsource(obj)
                                return f"{file_path}.{target_name}", source_code
                            except (TypeError, OSError):
                                pass  # 某些对象可能无法获取源代码
                    except Exception as e:
                        print(f"Error loading {file_path}: {e}")

        return None

    try:
        # 首先导入主包
        main_module = importlib.import_module(package_name)
        # 尝试在标准模块中查找
        result = _find_in_module(main_module, api_name)
        if result:
            return result

        # 如果未找到，尝试在文件系统中查找
        package_path = os.path.dirname(main_module.__file__)
        return _find_in_files(package_path, api_name)
    except ImportError as e:
        print(f"Error: Could not import package {package_name}: {e}")
        return None



def install_single_library(lib,version):
    """
    :param lib: package name eg: pandas
    :param version: verson number eg: 0.23.4
    :return:
    """
    print("=" * 30 + f" Installing requirements {lib}{version} " + "=" * 30)
    full_lib = lib + version
    try:
        # 根据自己系统配置重新调整
        pip_path = "pip"
        # pip_path = f'./venvs/{env_name}/bin/pip' if os.name != 'nt' else f'./venvs/{env_name}/Scripts/pip'
        subprocess.run([pip_path, 'install', full_lib, '-i',
                        'https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/'], check=True)
        print("=" * 30 + f" Requirements installed successfully for '{lib}'! " + "=" * 30)
        return True
    except subprocess.CalledProcessError:
        print('/' * 30 + f"Error: Failed to install requirements {lib}{version}" + '/' * 30)
        return False
def parse_function(func) -> Dict[str, Any]:
    """解析函数并返回结构化信息"""
    # 获取源码
    """
    :param func:(module)
    """


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


def get_module_obj(api_full_path:str):
    """
    :param api_full_path: the full path of an API
    eg. resolve_patterns_locally_or_by_urls the full path is datasets.data_files.resolve_patterns_locally_or_by_urls
    :return:
    """
    try:

        parts = api_full_path.split(".")
        module = importlib.import_module(parts[0])
        for part in parts[1:]:
            module = getattr(module, part)
        return module
    except (ModuleNotFoundError, AttributeError) as e:
        print(f"导入失败: {e}")
        return None


def is_in_dict(elem,dict):
    if not elem in dict:
        return False
    else:
        return True


def write_to_json(output_file,dict):
    with open(output_file,"w") as f:
        f.write(json.dumps(dict,indent=4))
    print(f"write into {output_file}")


if __name__ == '__main__':
    with open(requirement_apis_file) as f:
        data_dict = json.load(f)
        if "data" in data_dict.keys():
            data_lib_dict = data_dict["data"]
        else:
            data_lib_dict = data_dict
        libs = data_lib_dict.items()
    for item in libs:
        # 为每个库创建新的字典
        lib_res_dict = {}
        lib_err_dict = {}

        lib = item[0]

        for entry in item[1].items():
            version = entry[0]
            print(lib)
            print(version)

            if install_single_library(lib, version):
                if not isinstance(entry[1], list):
                    details = list(entry[1].keys())
                else:
                    details = entry[1]
                # import ipdb
                # ipdb.set_trace()
                for name in details:
                    try:
                        # lib_module = importlib.import_module(lib)
                        # api = getattr(lib_module, name)

                        module_path,source = find_api_definition(lib,name)
                        api = get_module_obj(module_path)
                        if not api:
                            raise AttributeError(f"API '{name}' not found in library '{lib}'")
                        parsed_info = parse_function(api)
                        # 使用库专用的字典
                        if not is_in_dict(lib, lib_res_dict):
                            lib_res_dict[lib] = {}
                        if not is_in_dict(version, lib_res_dict[lib]):
                            lib_res_dict[lib][version] = {}

                        lib_res_dict[lib][version][name] = parsed_info
                        print(f"Successful processing {lib} {version} {name}")

                    except Exception as e:
                        if lib not in lib_err_dict:
                            lib_err_dict[lib] = {}
                        if version not in lib_err_dict[lib]:
                            lib_err_dict[lib][version] = {}

                        lib_err_dict[lib][version][name] = str(e)  # 转换为字符串以确保可序列化
                        print(f"Error processing {lib} {version} {name}: {e}")

            else:
                if lib not in lib_err_dict:
                    lib_err_dict[lib] = {}
                lib_err_dict[lib][version] = entry[1]

        # 为每个库写入独立的文件，只包含该库的数据
        parsed_file = os.path.join(res_file_dir, f"parsed_{lib}_APIs.json")
        err_file = os.path.join(err_file_dir, f"err_{lib}_APIs.json")

        lib_res = {"data": lib_res_dict}
        lib_err = {"data": lib_err_dict}
        write_to_json(parsed_file, lib_res)
        write_to_json(err_file, lib_err)