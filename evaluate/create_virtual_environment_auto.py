import subprocess
import os
import shutil
import json
import re


def create_virtual_env(env_name, python_version):
    """Create a virtual environment with a specific Python version."""
    if not os.path.exists(f'../../venvs/{env_name}'):
        print("*" * 30 + f" Creating virtual environment '{env_name}' " + "*" * 30)
        subprocess.run([python_version, '-m', 'venv', f'../../venvs/{env_name}'], check=True)
        print("*" * 30 + f" Virtual environment '{env_name}' created successfully! " + "*" * 30)
    else:
        print('/' * 30 + f"Virtual environment '{env_name}' already exists." + '/' * 30)


def install_requirements(env_name, requirements_file):
    """Install requirements in the virtual environment."""
    print("=" * 30 + f" Installing requirements from '{requirements_file}' " + "=" * 30)
    try:
        subprocess.run([f'../../venvs/{env_name}/Scripts/pip', 'install', '-r', requirements_file], check=True)
        print("=" * 30 + f" Requirements installed successfully for '{env_name}'! " + "=" * 30)
        return True
    except subprocess.CalledProcessError:
        print('/' * 30 + f"Error: Failed to install requirements from '{requirements_file}'" + '/' * 30)
        return False


def clear_environment(env_name):
    """Clear the virtual environment by uninstalling all packages."""
    freeze_file = 'requirements_to_uninstall.txt'
    with open(freeze_file, 'w') as f:
        subprocess.run([f'../../venvs/{env_name}/Scripts/pip', 'freeze'], stdout=f, check=True)

    print("-" * 30 + f" Removing dependencies from '{env_name}' " + "-" * 30)
    subprocess.run([f'../../venvs/{env_name}/Scripts/pip', 'uninstall', '-y', '-r', freeze_file], check=True)
    print("-" * 30 + f" Dependencies removed successfully from '{env_name}'! " + "-" * 30)

    try:
        os.remove(freeze_file)
    except OSError as e:
        print(f"Error removing {freeze_file}: {e}")


def move_to_error_folder(requirements_file, error_folder):
    """Move the failed requirements.txt file to the error folder."""
    if not os.path.exists(error_folder):
        os.makedirs(error_folder)

    destination = os.path.join(error_folder, os.path.basename(requirements_file))
    shutil.move(requirements_file, destination)
    print(f"Moved '{requirements_file}' to '{error_folder}'")


def get_requires_python(requirements, key):
    """
    从要求的字典中提取特定键的 Python 最小版本号。

    :param requirements: 包含键值对的字典
    :param key: 要检索的键名
    :return: 提取的 Python 最小版本号（字符串），如果未找到则返回 None
    """
    if key in requirements:
        value = requirements[key]  # 获取键对应的值

        if value is not None:
            # 查找以 '>=' 开头的部分
            match = re.search(r'>=(\d+(\.\d+)*)(?:,\s*|\s*$)', value)

            if match:
                return match.group(1)  # 返回匹配的版本号

    return None  # 如果未找到，则返回 None


def get_python_version(requires_version):
    if requires_version is None:
        return 'C:/Users/27319/AppData/Local/Programs/Python/Python38/python.exe'
    else:
        version_parts = requires_version.split(".")
        requires_version = int("".join(version_parts[:2]))
        if requires_version < 35:
            return None
        if 35 <= requires_version < 36:
            return 'C:/Users/27319/AppData/Local/Programs/Python/Python35/python.exe'
        if 36 <= requires_version < 37:
            return 'C:/Users/27319/AppData/Local/Programs/Python/Python36/python.exe'
        if 37 <= requires_version < 38:
            return 'C:/Users/27319/AppData/Local/Programs/Python/Python37/python.exe'
        if 38 <= requires_version < 39:
            return 'C:/Users/27319/AppData/Local/Programs/Python/Python38/python.exe'
        if 39 <= requires_version < 310:
            return 'C:/Users/27319/AppData/Local/Programs/Python/Python39/python.exe'
        if 310 <= requires_version < 311:
            return 'C:/Users/27319/AppData/Local/Programs/Python/Python310/python.exe'
        if requires_version >= 311:
            return 'C:/Users/27319/AppData/Local/Programs/Python/Python311/python.exe'


def process_requirements_folder(requirements_folder, error_folder, low_version_folder, requirements_data):
    """Process all requirements.txt files in the given folder."""
    for requirements_file in os.listdir(requirements_folder):
        if requirements_file.endswith('.txt'):
            env_name = requirements_file.replace('requirements-', '').replace('.txt', '')

            # 获取适用python版本范围
            requires_python = get_requires_python(requirements_data, env_name)

            # 确定虚拟环境python版本
            python_version = get_python_version(requires_python)

            full_path = os.path.join(requirements_folder, requirements_file)

            if python_version:
                # Step 1: Create virtual environment
                create_virtual_env(env_name, python_version)

                # Step 2: Install the specified requirements
                if not install_requirements(env_name, full_path):
                    # If installation fails, move the file to the error folder
                    move_to_error_folder(full_path, error_folder)
            else:
                # Move the file to the low_version folder
                move_to_error_folder(full_path, low_version_folder)

            # # Step 3: Ask if the user wants to clear the environment
            # cont = input(f"Do you want to clear the virtual environment '{env_name}'? (yes/no): ")
            # if cont.lower() == 'yes':
            #     clear_environment(env_name)


def main():
    """Main function for automating the installation of dependencies."""
    requirements_folder = '../../requirements/all'
    error_folder = '../../requirements/error'
    low_version_folder = '../../requirements/low_version'
    libraries_requires_python_path = '../../requirements/libraries_requires_python_v3.json'

    # 指定python编译器版本
    with open(libraries_requires_python_path, 'r', encoding='utf-8') as f:
        requirements_data = json.load(f)

    # Process all requirements.txt files in the specified folder
    process_requirements_folder(requirements_folder, error_folder, low_version_folder, requirements_data)


if __name__ == '__main__':
    main()
