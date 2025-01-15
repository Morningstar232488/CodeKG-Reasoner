import os
import json


def save_task_functions(json_file, task_id_folder):
    # 读取JSON文件
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 遍历每条数据
    for item in data['data']:
        # 获取id、model_filled_code、test_cases、dependency和version的值
        task_id = item.get('id')
        model_filled_code = item.get('model_filled_code')
        test_cases = item.get('test_cases')
        dependency = item.get('dependency')
        version = item.get('version')
        core_token = item.get('answer')

        # without import
        imports = item.get('imports')

        # 检查id和model_filled_code是否存在
        if not task_id or not model_filled_code:
            print(f"Skipping entry with missing id or model_filled_code: {item}")
            continue

        task_id_file = os.path.join(task_id_folder, task_id)

        # 创建任务id对应的文件夹（如果不存在）
        os.makedirs(task_id_file, exist_ok=True)

        # 处理dependency和version，用于构造venv名称
        if dependency and version:
            venv_name = f"{dependency}-{version.lstrip('==')}"
        else:
            print(f"Skipping entry with missing dependency or version: {item}")
            continue

        # 遍历model_filled_code字典，创建对应的子文件夹和文件
        for index, code in model_filled_code.items():
            subfolder = os.path.join(task_id_file, f"{task_id}_{index}")
            os.makedirs(subfolder, exist_ok=True)

            # 拼接虚拟环境注释、task_function_code和test_cases，并写入test.py
            venvs_comment = f"# Virtual environment: {venv_name}"
            task_id_comment = f"# Task ID: {task_id}"
            core_token_comment = f"# Core Token: {core_token}"
            # combined_code = venvs_comment + "\n" + task_id_comment + "\n" + core_token_comment + "\n\n\n" + code + "\n\n\n" + (test_cases if test_cases else "")

            # without import
            combined_code = venvs_comment + "\n" + task_id_comment + "\n" + core_token_comment + "\n\n\n" + imports + "\n\n\n" + code + "\n\n\n" + (test_cases if test_cases else "")

            test_file_path = os.path.join(subfolder, "test.py")
            with open(test_file_path, 'w', encoding='utf-8') as test_file:
                test_file.write(combined_code)
            print(f"Saved combined code to {test_file_path}")

            # 创建run_test.py文件的路径
            run_test_file_path = os.path.join(subfolder, "run_test.py")

            # 构建run_test.py的内容
            run_test_content = f'''{venvs_comment}
{task_id_comment}

import subprocess
import os

def run_tests_in_virtualenv(venv, test_file):
    # 指定虚拟环境的路径
    venv_path = os.path.abspath(f"../../../../../venvs/{{venv}}/Scripts/activate.bat")

    # 指定要运行的测试脚本
    test_script = os.path.abspath(f"./{{test_file}}")

    # 创建激活虚拟环境并运行测试的命令
    command = f'cmd /k "{{venv_path}} && python {{test_script}} && exit"'

    # 运行命令
    subprocess.run(command, shell=True)

if __name__ == "__main__":
    venv = "{venv_name}"
    test_file = "test.py"
    run_tests_in_virtualenv(venv, test_file)
'''

            # 将run_test.py内容写入文件
            with open(run_test_file_path, 'w', encoding='utf-8') as run_test_file:
                run_test_file.write(run_test_content)
            print(f"Saved run_test.py to {run_test_file_path}")

if __name__ == '__main__':
    # 示例调用
    # model_name = 'Llama-3-70B'
    # index = '1'
    # task = 'block'
    # task_id_folder = f'../testing_pass@k_{model_name}_{index}_{task}_without_import'
    # json_file = f'../../../output_granularity_data/filter_with_info_v3/{model_name}/{index}/test_data_{task}_without_import.json'
    # save_task_functions(json_file, task_id_folder)

    # auto
    model_names = ['GPT-3.5', 'GPT-4o', 'Llama-3-70B']
    tasks = ['token', 'line', 'block']  # 定义三种不同的任务
    index = '1'

    for model_name in model_names:
        for task in tasks:
            print("【" * 50 + f"Writing {model_name}-{task} files" + "】" * 50)
            task_id_folder = f'../testing_pass@k_{model_name}_{index}_{task}_without_import_without_version'
            json_file = f'../../../output_granularity_data/filter_with_info_v3/{model_name}/{index}/test_data_{task}_without_import_without_version.json'
            save_task_functions(json_file, task_id_folder)
