#!/bin/bash

# ./rum_evaluate_migration Qwen/Qwen2.5-7B-Instruct-Turbo major minor

allowed_models=("Qwen/Qwen2.5-7B-Instruct-Turbo" "deepseek-ai/DeepSeek-V3" "Llama-3.3-70B-Instruct-Turbo" "Qwen/Qwen2.5-Coder-32B-Instruct" "meta-llama/Llama-2-13b-chat-hf")

# 检查 model_name 是否在允许的列表中
# shellcheck disable=SC2076
if [[ ! " ${allowed_models[*]} " =~ " ${model_name} " ]]; then
    echo "Error: The model_name '$model_name' is not allowed."
    echo "Allowed models are: ${allowed_models[*]}"
    exit 1
fi

# 检查是否提供了足够的参数
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 model_name edit_order_1 edit_order_2"
    exit 1
fi

# 获取参数
model_name=$1
edit_order_1=$2
edit_order_2=$3

# 依次执行三个 Python 脚本
echo "Running clear_ans_update.py..."
python clear_ans_update.py "$model_name" "$edit_order_1" "$edit_order_2"

echo "Running choose_core_line_from_block_versicode.py..."
python choose_core_line_from_block_versicode.py "$model_name" "$edit_order_1" "$edit_order_2"

echo "Running compute_migration_cdc.py..."
python compute_migration_cdc.py "$model_name" "$edit_order_1" "$edit_order_2"

echo "Pipeline execution completed."