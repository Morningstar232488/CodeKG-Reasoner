import os
import inspect
import importlib.util
from typing import Optional, Tuple

def find_api_definition(api_name: str, file_path: str) -> Optional[Tuple[str, str]]:
    """
    在指定文件中查找API的定义位置和源代码。

    Args:
        api_name (str): API名称，例如 'load_readme_description'
        file_path (str): 文件路径，例如 'pytorch-lightning-2.1.2/.actions/assistant.py'

    Returns:
        Optional[Tuple[str, str]]: 返回一个元组 (API完整路径, 源代码)，如果未找到则返回 None
    """
    try:
        # 从文件路径加载模块
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 检查模块中是否有目标API
        if hasattr(module, api_name):
            obj = getattr(module, api_name)
            try:
                source_code = inspect.getsource(obj)
                return f"{file_path}.{api_name}", source_code
            except (TypeError, OSError):
                print(f"Warning: Could not get source code for {api_name} in {file_path}")
                return None
        else:
            print(f"API {api_name} not found in {file_path}")
            return None

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


# 使用示例
if __name__ == "__main__":
    # 示例：在指定文件中查找 load_readme_description
    api_name = "experimental_distribute_datasets_from_function"
    file_path = "/Users/qingyuanzii/miniconda3/envs/py37/lib/python3.7/site-packages/tensorflow-2.1.2/tensorflow/python/distribute/central_storage_strategy.py"

    result = find_api_definition(api_name, file_path)
    if result:
        module_path, source = result
        print(f"Found {api_name} in {module_path}")
        print("\nSource code:")
        print(source)
    else:
        print(f"Could not find {api_name} in {file_path}")

