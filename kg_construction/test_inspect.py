import os
import importlib
import inspect
import importlib.util
from typing import Optional, Tuple
import pkgutil

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


# 使用示例
if __name__ == "__main__":

    # 示例：在tensorflow包中查找experimental_distribute_datasets_from_function
    package_name = "pytorch_lightning"
    api_name = "mean_squared_error"

    # # 重置 TensorFlow 默认计算图
    # import tensorflow as tf
    # tf.compat.v1.reset_default_graph()

    result = find_api_definition(package_name, api_name)
    if result:
        module_path, source = result
        print(f"Found {api_name} in {module_path}")
        print("\nSource code:")
        print(source)
    else:
        print(f"Could not find {api_name} in {package_name}")



# import os
# import importlib
# import inspect
# import importlib.util
# from typing import Optional, Tuple
# import pkgutil
#
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
#     def _find_in_files(package_path: str, target_name: str) -> Optional[Tuple[str, str]]:
#         """递归在文件系统中查找API"""
#         for root, dirs, files in os.walk(package_path):
#             # 忽略隐藏目录（以 . 开头的目录）
#             dirs[:] = [d for d in dirs if not d.startswith('.')]
#             for file in files:
#                 if file.endswith(".py"):
#                     file_path = os.path.join(root, file)
#                     try:
#                         # 从文件加载模块
#                         module_name = os.path.splitext(file)[0]
#                         spec = importlib.util.spec_from_file_location(module_name, file_path)
#                         module = importlib.util.module_from_spec(spec)
#                         spec.loader.exec_module(module)
#
#                         # 检查模块中是否有目标API
#                         if hasattr(module, target_name):
#                             obj = getattr(module, target_name)
#                             try:
#                                 source_code = inspect.getsource(obj)
#                                 return f"{file_path}.{target_name}", source_code
#                             except (TypeError, OSError):
#                                 pass  # 某些对象可能无法获取源代码
#                     except Exception as e:
#                         print(f"Error loading {file_path}: {e}")
#
#         return None
#
#     try:
#         # 首先导入主包
#         main_module = importlib.import_module(package_name)
#         # 尝试在标准模块中查找
#         result = _find_in_module(main_module, api_name)
#         if result:
#             return result
#
#         # 如果未找到，尝试在文件系统中查找
#         package_path = os.path.dirname(main_module.__file__)
#         return _find_in_files(package_path, api_name)
#     except ImportError as e:
#         print(f"Error: Could not import package {package_name}: {e}")
#         return None
#
#
# # 使用示例
# if __name__ == "__main__":
#     # 示例：在pytorch_lightning包中查找load_readme_description
#     package_name = "tensorflow"
#     api_name = "experimental_distribute_datasets_from_function"
#
#     result = find_api_definition(package_name, api_name)
#     if result:
#         module_path, source = result
#         print(f"Found {api_name} in {module_path}")
#         print("\nSource code:")
#         print(source)
#     else:
#         print(f"Could not find {api_name} in {package_name}")
# import pkgutil
# import importlib
# import inspect
# from typing import Optional, Tuple
#
#
#
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
#
#
# # 使用示例
#
#
# if __name__ == "__main__":
#     # 示例：在tensorflow包中查找keras
#     package_name = "pytorch_lightning"
#     api_name = "load_readme_description"
#
#     result = find_api_definition(package_name, api_name)
#     if result:
#         module_path, source = result
#         print(f"Found {api_name} in {module_path}")
#         print("\nSource code:")
#         print(source)
#     else:
#         print(f"Could not find {api_name} in {package_name}")
#
#
#
