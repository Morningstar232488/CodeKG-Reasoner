import os
import subprocess
import platform

def install_package_in_venv(library_name, version, package, wheel_file):
    # 构建虚拟环境路径
    venv_path = os.path.abspath(f"../../venvs/{library_name}-{version}")

    # 检查虚拟环境是否存在
    if not os.path.exists(venv_path):
        print(f"虚拟环境 {venv_path} 不存在，请确保路径正确。")
        return

    # 根据操作系统类型选择激活脚本路径
    if platform.system() == "Windows":
        print("Windows 环境检测到")
        activate_script = os.path.join(venv_path, 'Scripts', 'activate.bat')

        # 检查激活脚本是否存在
        if not os.path.exists(activate_script):
            print(f"虚拟环境 {venv_path} 中的激活脚本不存在。")
            return

        # Windows 下用 cmd /c 启动虚拟环境并安装包
        if package:
            # Install package from PyPI
            install_command = f'cmd /c "{activate_script} && pip install {package}"'
        elif wheel_file:
            # Install package from wheel file
            install_command = f'cmd /c "{activate_script} && pip install {wheel_file}"'
        else:
            print("No package or wheel file specified.")
            return

        try:
            subprocess.run(install_command, shell=True, check=True)
            print(f"{package} 安装成功。")
        except subprocess.CalledProcessError as e:
            print(f"{package} 安装失败，错误信息: {e}")
    else:
        # Linux/macOS 系统
        activate_script = os.path.join(venv_path, 'bin', 'activate')

        if not os.path.exists(activate_script):
            print(f"虚拟环境 {venv_path} 中的激活脚本不存在。")
            return

        # Linux/macOS 用 source 激活虚拟环境
        install_command = f"source {activate_script} && pip install {package}"

        try:
            subprocess.run(install_command, shell=True, check=True)
            print(f"{package} 安装成功。")
        except subprocess.CalledProcessError as e:
            print(f"{package} 安装失败，错误信息: {e}")


# 示例使用
library_name = 'librosa'
version = '0.6.3'
package = 'numba==0.48.0'
wheel_file = ''
install_package_in_venv(library_name, version, package, wheel_file)
