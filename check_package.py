import json
import os
import sys


def read_json(file_path):
    """读取 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(data, file_path):
    """写入 JSON 文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def find_missing_apis(parsed_apis, requirement_apis, package):
    """比较 API 并找出未出现的 API"""
    missing_apis = {}

    # 遍历 requirement_apis 中的每个版本
    for version, apis in requirement_apis['data'][package].items():
        missing_apis[version] = {}
        # 检查每个 API 是否在 parsed_apis 中
        for api in apis['names']:
            if api not in parsed_apis['data'][package].get(version, {}):
                missing_apis[version][api] = "err"

    return missing_apis


def main():
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("Usage: python script.py <package>")
        sys.exit(1)

    package = sys.argv[1]

    # 文件路径
    parsed_file_path = f'./kg_data/parsed_data/original_data/parsed_{package}_APIs.json'
    requirement_file_path_1 = f'./kg_data/requirement_APIs/requirement_libs_private/{package}_APIs.json'
    requirement_file_path_2 = f'./kg_data/requirement_APIs/requirement_libs/{package}_APIs.json'
    output_file_path = f'./kg_data/missing_APIs/missing_{package}_apis.json'

    # 读取 parsed_apis
    if not os.path.exists(parsed_file_path):
        print(f"Parsed APIs file {parsed_file_path} does not exist.")
        sys.exit(1)
    parsed_apis = read_json(parsed_file_path)

    # 初始化 missing_apis
    missing_apis = {}

    # 检查并处理 requirement_file_path_1
    if os.path.exists(requirement_file_path_1):
        requirement_apis_1 = read_json(requirement_file_path_1)
        missing_apis.update(find_missing_apis(parsed_apis, requirement_apis_1, package))

    # 检查并处理 requirement_file_path_2
    if os.path.exists(requirement_file_path_2):
        requirement_apis_2 = read_json(requirement_file_path_2)
        missing_apis.update(find_missing_apis(parsed_apis, requirement_apis_2, package))

    # 如果没有找到任何 missing_apis，退出
    if not missing_apis:
        print("No missing APIs found.")
        sys.exit(0)

    # 构造最终的 missing_apis 数据结构
    result = {"data": {package: missing_apis}}

    # 写入新的 JSON 文件
    write_json(result, output_file_path)

    print(f"未出现的 API 已存储到 {output_file_path}")


if __name__ == "__main__":
    main()