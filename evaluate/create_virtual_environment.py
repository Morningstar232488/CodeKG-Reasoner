import subprocess
import os


def create_virtual_env(env_name, python_version='python'):
    """Create a virtual environment with a specific Python version."""
    if not os.path.exists(env_name):
        print("*" * 30 + f"creating the virtual environment..." + "*" * 30)
        subprocess.run([python_version, '-m', 'venv', f'../../venvs/{env_name}'], check=True)
        print("*" * 30 + f"create the virtual environment successfully!" + "*" * 30)


def install_requirements(env_name, requirements_file):
    """Install requirements in the virtual environment."""
    print("=" * 30 + f"installing requirements..." + "=" * 30)
    subprocess.run([f'../../venvs/{env_name}/Scripts/pip', 'install', '-r', requirements_file], check=True)
    print("=" * 30 + f"install requirements successfully!" + "=" * 30)


def clear_environment(env_name):
    """Clear the virtual environment by uninstalling all packages."""
    freeze_file = 'requirements_to_uninstall.txt'
    with open(freeze_file, 'w') as f:
            subprocess.run([f'../../venvs/{env_name}/Scripts/pip', 'freeze'], stdout=f, check=True)

    print("-" * 30 + f"removing dependencies..." + "-" * 30)
    subprocess.run([f'../../venvs/{env_name}/Scripts/pip', 'uninstall', '-y', '-r', freeze_file], check=True)
    print("-" * 30 + f"remove dependencies successfully!" + "-" * 30)

    try:
        os.remove(freeze_file)
    except OSError as e:
        print(f"Error removing {freeze_file}: {e}")


def main():
    """Main function for manually installing and uninstalling dependencies."""
    env_name = 'librosa-0.6.3'
    requirements = f'../../requirements/all/{env_name}.txt'
    # 指定python编译器版本
    python_version = 'C:/Users/27319/AppData/Local/Programs/Python/Python36/python.exe'

    # Step 1: Create virtual environment (if it doesn't exist)
    create_virtual_env(env_name, python_version)

    # Step 2: Wait for manual requirements.txt file update
    input("Replace the requirements.txt file, then press Enter to continue...")

    # Step 3: Install the specified requirements
    install_requirements(env_name, requirements)

    # # Ask if you want to test another requirements.txt
    # cont = input("Do you want to test with another requirements.txt file? (yes/no): ")
    # if cont.lower() != 'yes':
    #     print(f"The current environment is maintained with the dependencies from the current requirements.txt file: {requirements}.")
    # else:
    #     # Step 4: Clear the environment (uninstall all packages)
    #     clear_environment(env_name)


if __name__ == '__main__':
    main()
