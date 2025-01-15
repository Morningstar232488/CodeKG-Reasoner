import json

# 读取 requirement_APIs.json 文件
requirement_apis_file = "../kg_data/requirement_APIs/requirement_APIs.json"
output_file = "../kg_data/requirement_APIs/requirement_APIs_private.json"

with open(requirement_apis_file, 'r') as f:
    data_dict = json.load(f)
    data_lib_dict = data_dict['data']

# 统计所有库的总数
total_libs = 0

# 遍历每个库及其版本
for lib, versions in data_lib_dict.items():
    # 创建一个新的字典，用于存储过滤后的版本
    filtered_versions = {}

    for version, details in versions.items():
        # 获取 names 列表
        names = details['names']

        # 过滤掉以 _ 开头的名称
        # filtered_names = [name for name in names if not name.startswith("_")]
        filtered_names = [name for name in names if name.startswith("_")]

        # 如果 filtered_names 不为空，则更新 details 并保留该版本
        if filtered_names:
            # 更新 names 列表
            details['names'] = filtered_names
            # 更新 count 值
            details['count'] = len(filtered_names)
            # 将该版本添加到 filtered_versions 中
            filtered_versions[version] = details
            # 更新总数
            total_libs += 1

    # 更新库的版本信息
    data_lib_dict[lib] = filtered_versions

# 将修改后的数据写回文件
with open(output_file, 'w') as f:
    json.dump(data_dict, f, indent=4)

# 输出统计结果
print(f"所有库的总数: {total_libs}")
print("已更新 count 值，删除 names 为空的版本，并更新了文件。")