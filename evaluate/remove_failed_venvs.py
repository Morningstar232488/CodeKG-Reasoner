import os
import shutil

# txt 文件夹路径
txt_folder = ("../../requirements/error")
# 子文件夹所在的文件夹路径
subfolder_directory = "../../venvs"

# 遍历 txt 文件夹中的文件
for txt_file in os.listdir(txt_folder):
    if txt_file.endswith(".txt"):
        # 提取 txt 文件名中的 package-version 部分
        package_version = txt_file.replace("requirements-", "").replace(".txt", "")

        # 构造子文件夹路径
        subfolder_path = os.path.join(subfolder_directory, package_version)

        # 检查子文件夹是否存在
        if os.path.isdir(subfolder_path):
            print(f"Deleting folder: {subfolder_path}")
            shutil.rmtree(subfolder_path)  # 删除子文件夹
        else:
            print(f"Folder not found: {subfolder_path}")
