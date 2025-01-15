import subprocess
import os
import shutil
import json
import re

class VirtualEnvManager:
    def __init__(self, requirements_folder, error_folder, low_version_folder):
        """
        初始化 VirtualEnvManager 类。

        :param requirements_folder: 包含 requirements.txt 文件的文件夹路径
        :param error_folder: 安装失败的 requirements.txt 文件存放路径
        :param low_version_folder: Python 版本过低的 requirements.txt 文件存放路径
        :param libraries_requires_python_path: 包含库及其 Python 版本要求的 JSON 文件路径
        """
        self.requirements_folder = requirements_folder
        self.error_folder = error_folder
        self.low_version_folder = low_version_folder

        # self.libraries_requires_python_path = libraries_requires_python_path

    def create_virtual_env(self, env_name, python_version):
        """创建虚拟环境。"""
        if not os.path.exists(f'./venvs/{env_name}'):
            print("*" * 30 + f" Creating virtual environment '{env_name}' " + "*" * 30)
            subprocess.run([python_version, '-m', 'venv', f'./venvs/{env_name}'], check=True)
            print("*" * 30 + f" Virtual environment '{env_name}' created successfully! " + "*" * 30)

            self.venv_path = f"./venvs/{env_name}"
        else:
            print('/' * 30 + f"Virtual environment '{env_name}' already exists." + '/' * 30)
    def install_single_requirement(self,env_name,lib,version):
        """在虚拟环境中安装 requirements.txt 文件中的依赖。"""
        print("=" * 30 + f" Installing requirements {lib}{version} " + "=" * 30)
        full_lib = lib+version
        try:
            # 根据自己系统配置重新调整
            # pip_path = f'./venvs/{env_name}/bin/pip' if os.name != 'nt' else f'./venvs/{env_name}/Scripts/pip'
            pip_path = f'./venvs/{env_name}/bin/pip'
            subprocess.run([pip_path, 'install',full_lib, '-i',
                            'https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/'], check=True)
            print("=" * 30 + f" Requirements installed successfully for '{env_name}'! " + "=" * 30)
            return True
        except subprocess.CalledProcessError:
            print('/' * 30 + f"Error: Failed to install requirements {lib}{version}" + '/' * 30)
            return False

    def install_requirements(self, env_name, requirements_file):
        """在虚拟环境中安装 requirements.txt 文件中的依赖。"""
        print("=" * 30 + f" Installing requirements from '{requirements_file}' " + "=" * 30)
        try:
            # 根据自己系统配置重新调整
            # pip_path = f'./venvs/{env_name}/bin/pip' if os.name != 'nt' else f'./venvs/{env_name}/Scripts/pip'
            pip_path = f'./venvs/{env_name}/bin/pip'
            subprocess.run([pip_path, 'install', '-r', requirements_file,'-i','https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/'], check=True)
            print("=" * 30 + f" Requirements installed successfully for '{env_name}'! " + "=" * 30)
            return True
        except subprocess.CalledProcessError:
            print('/' * 30 + f"Error: Failed to install requirements from '{requirements_file}'" + '/' * 30)
            return False

    def clear_environment(self, env_name):
        """清除虚拟环境中的所有依赖。"""
        freeze_file = 'requirements_to_uninstall.txt'
        with open(freeze_file, 'w') as f:
            pip_path = f'./venvs/{env_name}/bin/pip' if os.name != 'nt' else f'./venvs/{env_name}/Scripts/pip'
            subprocess.run([pip_path, 'freeze'], stdout=f, check=True)

        print("-" * 30 + f" Removing dependencies from '{env_name}' " + "-" * 30)
        subprocess.run([pip_path, 'uninstall', '-y', '-r', freeze_file], check=True)
        print("-" * 30 + f" Dependencies removed successfully from '{env_name}'! " + "-" * 30)

        try:
            os.remove(freeze_file)
        except OSError as e:
            print(f"Error removing {freeze_file}: {e}")

    def destroy_virtual_env(self, env_name):
        """销毁（删除）虚拟环境。"""
        env_path = f'./venvs/{env_name}'
        if os.path.exists(env_path):
            print("*" * 30 + f" Destroying virtual environment '{env_name}' " + "*" * 30)
            shutil.rmtree(env_path)
            print("*" * 30 + f" Virtual environment '{env_name}' destroyed successfully! " + "*" * 30)
        else:
            print('/' * 30 + f"Virtual environment '{env_name}' does not exist." + '/' * 30)

    def move_to_error_folder(self, requirements_file, error_folder):
        """将失败的 requirements.txt 文件移动到错误文件夹。"""
        if not os.path.exists(error_folder):
            os.makedirs(error_folder)

        destination = os.path.join(error_folder, os.path.basename(requirements_file))
        shutil.move(requirements_file, destination)
        print(f"Moved '{requirements_file}' to '{error_folder}'")

    def get_requires_python(self, requirements, key):
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

    def get_python_version(self, requires_version):
        """根据 Python 版本要求获取对应的 Python 解释器路径。"""
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

    def process_requirements_folder(self):
        """处理指定文件夹中的所有 requirements.txt 文件。"""
        # with open(self.libraries_requires_python_path, 'r', encoding='utf-8') as f:
        #     requirements_data = json.load(f)

        for requirements_file in os.listdir(self.requirements_folder):

            env_name = requirements_file.replace('.txt', '')
            self.env_name = env_name
            # 获取适用 Python 版本范围
            # requires_python = self.get_requires_python(requirements_data, env_name)

            # 确定虚拟环境 Python 版本
            # python_version = self.get_python_version(requires_python)

            full_path = os.path.join(self.requirements_folder, requirements_file)
            # 简单起见，考虑单版本python
            python_version = "python"
            # if python_version:
            # Step 1: 创建虚拟环境
            self.create_virtual_env(env_name, python_version)

            # Step 2: 安装 requirements.txt 中的依赖
            if not self.install_requirements(env_name, full_path):
                # 如果安装失败，将文件移动到错误文件夹
                self.move_to_error_folder(full_path, self.error_folder)
            # else:
            #     # 将文件移动到低版本文件夹
            #     self.move_to_error_folder(full_path, self.low_version_folder)

    def install_lib(self,lib_name,lib_version,python_version):
        env_name = lib_name+lib_version
        self.create_virtual_env(env_name,python_version)
        self.install_single_requirement(env_name,lib_name,lib_version)


def main():
    """主函数，用于自动化安装依赖。"""
    requirements_folder = '../requirements_venv'
    error_folder = '../error'
    low_version_folder = '../low_version'
    # libraries_requires_python_path = './libraries_requires_python.json'

    # 创建 VirtualEnvManager 实例并处理 requirements.txt 文件
    env_manager = VirtualEnvManager(requirements_folder, error_folder, low_version_folder)
    env_manager.process_requirements_folder()

    # 示例：销毁虚拟环境
    # env_name_to_destroy = 'example_env'
    # env_manager.destroy_virtual_env(env_name_to_destroy)


if __name__ == '__main__':
    main()