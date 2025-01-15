import os
import ast
import importlib.util
import json
from create_venv import VirtualEnvManager
import time

"""
extract APIs from a library in the python interpreter from __init__.py
"""

# def install_package(package_name):
#     """
#     :param package_name: {package}=={version}(str)
#     :return: None
#     """
#     try:
#         print(f"Installing: {package_name}")
#         subprocess.check_call([sys.executable, "-m", "pip", "install", package_name,"-i" "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"])
#         print(f"{package_name} successfully installed")
#     except subprocess.CalledProcessError as e:
#         print(f"{package_name} failure: {e}")
#         sys.exit(1)

import subprocess
import sys

def find_module_path(venv_path, module_name):
    """
    使用虚拟环境的 Python 解释器查找模块路径。

    :param venv_path: 虚拟环境的路径
    :param module_name: 模块名
    :return: 模块路径（如果找到），否则返回 None
    """
    # 确定虚拟环境的 Python 解释器路径
    if sys.platform == "win32":
        python_path = f"{venv_path}/Scripts/python.exe"
    else:
        python_path = f"{venv_path}/bin/python"

    # 构造 Python 脚本
    script = f"""
import importlib.util

spec = importlib.util.find_spec("{module_name}")
if spec is not None:
    print(spec.origin)
else:
    print("Module not found")
    """

    # 调用虚拟环境的 Python 解释器
    result = subprocess.run([python_path, "-c", script], capture_output=True, text=True)
    # import ipdb
    # ipdb.set_trace()
    if result.stdout.strip() == "Module not found":
        return None
    return result.stdout.strip()


def find_init_file(package_name,package_path):
    """
    根据包名动态查找其 __init__.py 文件的路径。

    Args:
        package_name (str): 包名
        venv_path (str):python解释器路径

    Returns:
        str: __init__.py 文件路径
    """
    # 获取包的加载信息
    # 从创建好的隔离的环境里找到package
    # package_spec = importlib.util.find_spec(package_name.split('==')[0])

    # import ipdb
    # ipdb.set_trace()
    package_spec = importlib.util.spec_from_file_location(package_name, package_path)

    # if package_spec is None:
    #     print(f"{package_name} has not installed")
    #     install_package(package_name)

    time.sleep(1)

    if package_spec is None:
        raise FileNotFoundError("can not find: {}".format(package_name))

    # 获取包的路径
    package_path = package_spec.origin

    # 检查路径是否为目录形式的包
    if package_path.endswith('__init__.py'):
        # 如果直接是 __init__.py，返回它
        return package_path
    elif os.path.isdir(package_path):
        # 如果是文件夹形式，检查是否存在 __init__.py
        init_file_path = os.path.join(package_path, '__init__.py')
        if os.path.exists(init_file_path):
            return init_file_path
    elif package_path.endswith('.py'):
        # 如果是单个文件的模块，返回文件本身
        return package_path

    raise FileNotFoundError("未找到 {} 的有效 __init__.py 文件或入口模块".format(package_name))


def extract_imported_apis(init_file_path):
    """
    从 __init__.py 中提取出所导入的 API（类或函数）。

    Args:
        init_file_path (str): __init__.py 文件路径

    Returns:
        dict: 包含直接导入的模块和显式导入的类/函数
    """
    if not os.path.exists(init_file_path):
        raise FileNotFoundError(f"File not found: {init_file_path}")

    with open(init_file_path, "r", encoding="utf-8") as f:
        init_content = f.read()

    # 使用 AST 解析 Python 文件
    tree = ast.parse(init_content)
    imports = {"modules": [], "apis": []}

    for node in ast.walk(tree):
        # 处理 import 语句
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports["modules"].append(alias.name)
        # 处理 from ... import ... 语句
        elif isinstance(node, ast.ImportFrom):
            if node.module:  # 确保模块名存在
                for alias in node.names:
                    imports["apis"].append(f"{node.module}.{alias.name}")

    return imports


def save_to_json(data, output_file):
    """
    将数据保存为 JSON 文件。

    Args:
        data (dict): 要保存的数据
        output_file (str): 输出 JSON 文件路径
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("数据已保存到 {}".format(output_file))


# 示例：自动查找包的 __init__.py 文件并提取信息
if __name__ == "__main__":
    # try:
    #     _version = package_name.__version__
    # except:
    #     _version = version(package_name)
    # 待提取的包的路径
    requirements_folder = '../requirements_venv'
    # requirements_folder 中包含 "{package}-{version}.txt",内容为需要的package
    error_folder = '../error'
    low_version_folder = '../low_version'
    # libraries_requires_python_path = './libraries_requires_python.json'
    # 创建 VirtualEnvManager 实例并处理 requirements.txt 文件
    env_manager = VirtualEnvManager(requirements_folder, error_folder, low_version_folder)
    env_manager.process_requirements_folder()

    # 第一个参数用于读取package name
    package = env_manager.env_name
    parts = package.split("-")
    package_name = parts[0]
    version = parts[1] if len(parts) > 1 else None


    output_file = "../kg_data/{}_APIs_in_init_%s.json".format(package_name) % version  # 输出 JSON 文件


    # 定义结果字典，包含模块、API 和错误信息
    result = {"modules": [], "apis": [], "errors": ""}

    try:
        package_path = find_module_path(env_manager.venv_path,package_name)
        init_file_path = find_init_file(package_name,package_path)
        print("找到 {} 的 __init__.py 文件: {}".format(package_name, init_file_path))

        extracted_data = extract_imported_apis(init_file_path)
        result["modules"] = extracted_data["modules"]
        result["apis"] = extracted_data["apis"]

    except Exception as e:
        # 捕获错误并记录到结果中
        error_message = str(e)
        result["errors"] = error_message
        print("发生错误: {}".format(error_message))

    # 保存结果到 JSON 文件
    save_to_json(result, output_file)
