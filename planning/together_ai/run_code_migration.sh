#!/bin/bash

allowed_models=("Qwen/Qwen2.5-7B-Instruct-Turbo" "deepseek-ai/DeepSeek-V3" "meta-llama/Meta-Llama-3-70B-Instruct-Turbo" "Qwen/Qwen2.5-Coder-32B-Instruct" "meta-llama/Llama-2-13b-chat-hf")

# 检查是否提供了足够的参数
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 model_name"
    echo "Allowed models are: ${allowed_models[*]}"
    exit 1
fi

# 获取参数
model_name=$1

# 检查 model_name 是否在允许的列表中
# shellcheck disable=SC2076
if [[ ! " ${allowed_models[*]} " =~ " ${model_name} " ]]; then
    echo "Error: The model_name '$model_name' is not allowed."
    echo "Allowed models are: ${allowed_models[*]}"
    exit 1
fi

# 获取参数
model_name=$1


# 依次执行三个 Python 脚本
echo "Running code_migration.py"
python code_migration.py "$model_name"

echo "Running code_migration_exe.py"
python code_migration_exe.py "$model_name"

echo "Pipeline execution completed."