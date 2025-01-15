import json
import ast
import time

import sys

# 模拟文件路径
file_path = sys.argv[1]

# 读取文件内容
# 使用模拟数据代替实际文件读取
def load_json(file_path):
    # 实际代码应使用如下方式读取
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    # 这里使用模拟数据来演示
    return data


# 保存清理后的数据到新的 JSON 文件
def save_json(data, file_path):
    # 实际代码应使用如下方式保存
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


# 清理模型输出
def clean_model_outputs(data, file_path):
    for entry in data["data"]:
        cleaned_outputs = []
        # 字符串转为列表
        model_output_list = ast.literal_eval(entry["model_output"])
        for output in model_output_list:
            # 替换字符串中的特定模式
            # token、line
            # cleaned_output = output.replace("```python\n", "").replace("\n```", "").replace("```\n", "").replace("```\npython", "").replace("python\n", "").replace("```", "").strip()

            # block
            cleaned_output = output.replace("```python\n", "").replace("\n```", "").replace("```\n", "").replace("```\npython", "").replace("python\n", "").replace("```", "")

            # cleaned_output = output.replace("```python\n", "").replace("\n```", "")
            cleaned_outputs.append(cleaned_output)
        entry["model_output_clear"] = cleaned_outputs

    save_json(data, file_path)


# 加载数据
data = load_json(file_path)

# 清理数据
clean_model_outputs(data, file_path)

