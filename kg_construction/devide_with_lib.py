import json
import os

# 文件路径
requirement_apis_file = "../kg_data/requirement_APIs/requirement_APIs.json"
# output_file_dir = "../kg_data/requirement_APIs/requirement_libs_private"
output_file_dir = "../kg_data/requirement_APIs/req_lib"

# 确保输出目录存在
os.makedirs(output_file_dir, exist_ok=True)

# 读取 requirement_APIs.json 文件
with open(requirement_apis_file, 'r') as f:
    data_dict = json.load(f)
    data_lib_dict = data_dict['data']
    libs = data_lib_dict.items()

    # 遍历每个库
    for lib, versions in libs:
        # 构建库的数据结构
        lib_data = {
            lib: versions
        }

        # 构建输出文件路径
        output_file = os.path.join(output_file_dir, f"{lib}_APIs.json")

        # 将数据写入文件
        res = {"data":lib_data}
        with open(output_file, 'w') as f:
            json.dump(res, f, indent=4)
        print(f"Data written to {output_file}")