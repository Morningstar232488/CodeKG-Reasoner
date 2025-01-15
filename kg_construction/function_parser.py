import inspect
import docstring_parser
import sys
import importlib
import os
import subprocess
from typing import Dict, Any

class FunctionParser:
    """解析函数并返回结构化信息的类"""

    def __init__(self, venv_python_path,lib,func):
        self.venv_python_path = venv_python_path
        self.lib = lib
        self.func = func
        # venv_python = os.path.join(venv_path,'bin/python')
        script = f"""
import importlib
import inspect

try:
    module = importlib.import_module("{lib}")
    api = getattr(module,"{func}")
    print(inspect.getsource(api))
except ImportError as e:
    print(f"导入模块失败: {{e}}")
"""


        result = subprocess.run([self.venv_python_path, "-c", script], capture_output=True, text=True)
        print(result)

        self.source_code = result.stdout
        return self.source_code

    def parse(self) -> Dict[str, Any]:
        """解析函数并返回结构化信息"""
        # 获取源码
        source_code = self.source_code

        # 获取函数签名
        signature = inspect.signature(self.func)
        parameters = self._parse_parameters(signature)

        # 获取文档字符串
        docstring = inspect.getdoc(self.func)
        parsed_docstring = docstring_parser.parse(docstring) if docstring else None

        # 解析返回值描述
        returns_doc = self._parse_returns_doc(parsed_docstring)

        # 解析异常描述
        raise_doc = self._parse_raise_doc(parsed_docstring)

        # 构建结果
        result = {
            "_id": f"{self.func.__module__}.{self.func.__qualname__}",
            "doc": docstring,
            "is_deprecated": "deprecated" in (docstring or "").lower(),
            "is_addition": "addition" in (docstring or "").lower(),
            "source_code": source_code,
            "signature": str(signature),
            "parameters": parameters,
            "returns_doc": returns_doc,
            "raise_doc": raise_doc,
            "type": "member_function" if "." in self.func.__qualname__ else "function",
            "class": self.func.__qualname__.split(".")[0] if "." in self.func.__qualname__ else None
        }
        return result

    def _parse_parameters(self, signature) -> Dict[str, Dict[str, Any]]:
        """解析函数参数"""
        parameters = {}
        for name, param in signature.parameters.items():
            parameters[name] = {
                "description": None,  # 可以从文档字符串中解析
                "is_optional": param.default != inspect.Parameter.empty
            }
        return parameters

    def _parse_returns_doc(self, parsed_docstring) -> str:
        """解析返回值描述"""
        if parsed_docstring and parsed_docstring.returns:
            return parsed_docstring.returns.description
        return None

    def _parse_raise_doc(self, parsed_docstring) -> list:
        """解析异常描述"""
        if parsed_docstring and parsed_docstring.raises:
            return [r.description for r in parsed_docstring.raises]
        return None

"""FunctionParser.parse()"""