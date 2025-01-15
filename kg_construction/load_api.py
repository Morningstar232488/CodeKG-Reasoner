import importlib
import json
import os.path
import subprocess
import inspect
import docstring_parser
from typing import Dict, Any, Optional,Tuple
import pkgutil

# requirement_apis_file = f"../kg_data/requirement_APIs/requirement_APIs_update.json"
requirement_apis_file = f"../kg_data/requirement_APIs/req_lib/librosa_APIs.json"
res_file_dir = f"../kg_data/parsed_data/original_data"
err_file_dir = f"../kg_data/parsed_data/err_APIs"

res_dict = {}
err_dict = {}

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

    try:
        # 首先导入主包
        main_module = importlib.import_module(package_name)
        return _find_in_module(main_module, api_name)
    except ImportError as e:
        print(f"Error: Could not import package {package_name}: {e}")
        return None

def find_api_in_submodules(module, api_name: str) -> Optional[Any]:
    """
    在模块及其子模块中查找目标 API。
    :param module: 模块对象
    :param api_name: 目标 API 名称
    :return: 找到的 API 对象，如果未找到则返回 None
    """
    try:
        # 尝试在当前模块中获取 API
        api = getattr(module, api_name)
        return api
    except AttributeError:
        pass  # 如果未找到，继续查找子模块

    # 遍历所有子模块
    for _, submodule_name, is_pkg in pkgutil.iter_modules(module.__path__):
        try:
            # 导入子模块
            submodule = importlib.import_module(f"{module.__name__}.{submodule_name}")
            # 递归查找子模块
            api = find_api_in_submodules(submodule, api_name)
            if api is not None:
                return api
        except (ImportError, AttributeError):
            continue  # 如果子模块无法导入，跳过

    return None  # 如果未找到，返回 None

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
        data_lib_dict = data_dict['data']
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
                for name in entry[1]["names"]:
                    try:
                        lib_module = importlib.import_module(lib)
                        api = getattr(lib_module, name)
                        # module_path, source = find_api_definition(lib, name)
                        # api = get_module_obj(module_path)

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
        lib_res = {"data":lib_res_dict}
        lib_err = {"data":lib_err_dict}
        write_to_json(parsed_file, lib_res)
        write_to_json(err_file, lib_err)