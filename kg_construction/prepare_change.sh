#!/bin/bash

# 定义 name_list 数组
name_list=("major_to_major" "major_to_minor" "minor_to_major" "minor_to_minor" "code_migration_exe_new_to_old" "code_migration_exe_old_to_new")

# 遍历每个 JSON 文件
for name in "${name_list[@]}"; do
  # JSON 文件路径
  JSON_FILE="../datasets/code_migration/original/$name.json"

  # 检查 JSON 文件是否存在
  if [ ! -f "$JSON_FILE" ]; then
    echo "JSON file $JSON_FILE does not exist. Skipping..."
    continue
  fi

  # 使用 jq 提取 data 数组中的每个对象
  packages=$(jq -c '.data[]' "$JSON_FILE")

  # 遍历每个包
  echo "$packages" | while IFS= read -r package; do
      # 提取字段
      package_name=$(echo "$package" | jq -r '.dependency')

      # 根据 name 的值决定 original_version 和 target_version 的赋值逻辑
      if [[ "$name" == *"old_to_new"* ]]; then
          original_version=$(echo "$package" | jq -r '.old_version')
          target_version=$(echo "$package" | jq -r '.new_version')
      elif [[ "$name" == *"new_to_old"* ]]; then
          original_version=$(echo "$package" | jq -r '.new_version')
          target_version=$(echo "$package" | jq -r '.old_version')
      else
          # 默认情况（如果 name 不包含 old_to_new 或 new_to_old）
          original_version=$(echo "$package" | jq -r '.old_version')
          target_version=$(echo "$package" | jq -r '.new_version')
      fi

      # 打印提取的信息（可选）
      echo "Processing: $package_name, Original Version: $original_version, Target Version: $target_version"

      # 执行 Python 脚本
      python extract_APIs_by_evolution_patterns.py "$package_name" "$original_version" "$target_version"
  done
done