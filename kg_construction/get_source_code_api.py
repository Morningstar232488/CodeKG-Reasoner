import importlib

# package_name = 'click'
# api_name = 'resultcallback'


# package = importlib.import_module("datasets")


# 获取 API 对象
# api = getattr(package, api_name)
# print(f"Successfully imported {api_name} from {package_name}")


# import docstring_parser
# from typing import Dict, Any

import inspect
from typing import Dict, Any, Optional, Tuple
import docstring_parser
import importlib
import os
import ast


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


# 使用示例
if __name__ == "__main__":
    result = find_and_parse_api("jedi", "docstrings._strip_rest_role")

    if result:
        import json

        print(json.dumps(result, indent=2))
    else:
        print("API not found")

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



# 解析方法信息
# parsed_info = parse_function(jedi.docstring._strip_rest_role)
parsed_info = find_and_parse_api("pytorch_lightning","metrics.functional.mean_squared_error")

# 打印结果
import json
print(json.dumps(parsed_info, indent=4))
