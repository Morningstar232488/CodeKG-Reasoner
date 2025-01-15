import json
import os

# 初始化结果字典
res_dic = {}  # 存储每个 dependency 对应的所有版本（整合 old_versions 和 new_versions）

# 输入目录
input_dir = '/Volumes/kjz-SSD/Datasets/VersiCode/data/VersiCode_Benchmark/VersiCode_Benchmark/code_migration/original'

# 遍历目录
for root, dirs, files in os.walk(input_dir):
    for file in files:
        # 只处理 JSON 文件
        if file.endswith('.json'):
            file_path = os.path.join(root, file)
            print(f"Processing file: {file_path}")

            try:
                # 读取 JSON 文件
                with open(file_path, "r") as f:
                    _data = json.load(f)

                # 提取 data 字段
                data_list = _data.get("data", [])  # 如果 data 字段不存在，返回空列表

                # 遍历 data 列表
                for item in data_list:
                    dependency = item.get("dependency")
                    old_version = item.get("old_version")
                    new_version = item.get("new_version")

                    # 如果 dependency 不存在于结果字典中，初始化它的结构
                    if dependency not in res_dic:
                        res_dic[dependency] = {
                            "versions": set()  # 使用集合存储所有版本，避免重复
                        }

                    # 添加 old_version 和 new_version 到 versions 集合
                    if old_version:
                        res_dic[dependency]["versions"].add(old_version)
                    if new_version:
                        res_dic[dependency]["versions"].add(new_version)

            except json.JSONDecodeError:
                print(f"Error decoding JSON file: {file_path}")
            except KeyError as e:
                print(f"KeyError in file {file_path}: {e}")
            except Exception as e:
                print(f"Unexpected error in file {file_path}: {e}")

# 将集合转换为列表（因为 JSON 不支持集合）
for dependency, versions in res_dic.items():
    versions["versions"] = list(versions["versions"])

# 输出文件路径
output_file = '../kg_data/requirement_lib.json'

# 将结果保存到 JSON 文件
with open(output_file, 'w') as of:
    json.dump(res_dic, of, indent=4)

print(f"Results saved to {output_file}")