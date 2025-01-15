import json
from collections import defaultdict
import os
from packaging.specifiers import SpecifierSet
from packaging.version import Version

# 定义库的 Python 版本要求文件路径
lib_require_content_dir = "/Volumes/kjz-SSD/Datasets/VersiCode/data/VersiCode_Benchmark/VersiCode_Benchmark/code_migration/code_migration_exe/requirements/libraries_requires_python"

def find_require_python_version(lib_name: str, version: str, lib_require_content_dir: str):
    """
    根据库的名称和版本，找到兼容的 Python 版本。
    :param lib_name: 库的名称
    :param version: 库的版本
    :param lib_require_content_dir: 库的 Python 版本要求文件路径
    :return: 兼容的 Python 版本（字符串，例如 "3.8"），如果没有找到则返回 None
    """
    candidate_versions = [
        "3.10",  # 较新的版本
        "3.9",   # 较新的稳定版本
        "3.8",   # 较新的稳定版本
        "3.7",   # 较新的稳定版本
        "3.6",   # 较新的稳定版本
        "3.5",   # 较新的稳定版本
        "2.7",   # 最低支持的版本
    ]

    # 构建库的 JSON 文件路径
    lib_req_path = os.path.join(lib_require_content_dir, lib_name + ".json")

    # 如果文件不存在，返回 None
    if not os.path.exists(lib_req_path):
        print(f"Warning: No version requirements found for {lib_name}")
        return None

    # 加载库的 Python 版本要求
    with open(lib_req_path, 'r') as f:
        data_dict = json.load(f)

    # 构建库的唯一标识符（例如 "pandas-0.23.4"）
    lib = lib_name + version.replace("==", "-")

    # 如果库的版本要求不存在，返回 None
    if lib not in data_dict:
        print(f"Warning: No version requirements found for {lib}")
        return None

    # 获取库的 Python 版本约束
    constraints = data_dict[lib]

    # 如果约束为 "null" 或 None，默认返回最高支持的 Python 版本
    if constraints == "null" or constraints is None:
        print(f"Warning: Constraints for {lib} are null or None, defaulting to 3.10")
        return "3.10"

    # 确保 constraints 是字符串
    if not isinstance(constraints, str):
        print(f"Warning: Invalid constraints for {lib}: {constraints}")
        return None

    # 解析约束
    try:
        specifier = SpecifierSet(constraints)
    except Exception as e:
        print(f"Warning: Failed to parse constraints for {lib}: {e}")
        return None

    # 遍历候选 Python 版本，找到第一个兼容的版本
    for version in candidate_versions:
        if Version(version) in specifier:
            print(f"Found compatible Python version for {lib}: {version}")
            return version

    # 如果没有找到兼容的版本，返回 None
    print(f"Warning: No compatible Python version found for {lib} with constraints: {constraints}")
    return None

# 读取 requirement_APIs.json 文件
with open('../kg_data/requirement_APIs/requirement_APIs_update.json', 'r') as f:
    data = json.load(f)

# 存储每个 Python 版本下的库及其版本号
python_version_libraries = defaultdict(list)

# 遍历每个库及其版本
for lib, versions in data['data'].items():
    for version, details in versions.items():
        # 获取该库在该版本下兼容的 Python 版本
        python_version = find_require_python_version(lib, version, lib_require_content_dir)

        # 如果没有找到兼容的 Python 版本，跳过当前库版本
        if python_version is None:
            continue

        # 去掉 version 中已有的 "=="，确保最终结果只有两个等号
        version_cleaned = version.replace("==", "")
        lib_with_version = f"{lib}=={version_cleaned}"  # 携带版本号
        python_version_libraries[python_version].append(lib_with_version)

# 将结果转换为 JSON 格式
result = {python_version: libraries for python_version, libraries in python_version_libraries.items()}

# 输出结果
with open("classified_libraries.json",'w') as f:
    f.write(json.dumps(result, indent=4))