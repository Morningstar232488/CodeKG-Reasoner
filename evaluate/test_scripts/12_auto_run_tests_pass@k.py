import os
import subprocess
import json
import re


def extract_virtualenv_name(test_file):
    """从test.py文件的注释中提取虚拟环境名称"""
    with open(test_file, 'r', encoding='utf-8') as file:
        first_line = file.readline().strip()
        # 匹配 "Virtual environment: " 后面的部分
        match = re.match(r'# Virtual environment: (.+)', first_line)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"无法在 {test_file} 中找到虚拟环境名称")


def run_tests(directory, json_file):
    # 加载JSON文件，检查哪些任务已完成
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
        completed_tests = {item['id']: item for item in data['data'] if 'test_results' in item}

    # 指定目录下查找以task_id命名的子目录
    task_dirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

    # 遍历找到的每个task目录
    for task_dir in task_dirs:
        task_dir_path = os.path.join(directory, task_dir)

        # 在每个task目录下再查找子目录（如task_id_1, task_id_2等）
        sub_dirs = [sub_d for sub_d in os.listdir(task_dir_path) if os.path.isdir(os.path.join(task_dir_path, sub_d))]

        for sub_dir in sub_dirs:
            sub_dir_path = os.path.join(task_dir_path, sub_dir)
            test_file = os.path.join(sub_dir_path, 'test.py')

            # 提取虚拟环境名称
            virtualenv_name = extract_virtualenv_name(test_file)

            # 检查是否已完成测试
            task_id = f"{task_dir}"
            if task_id in completed_tests:
                print(f"Skipping completed test for {task_id}")
                continue  # 跳过已完成的测试

            # 构建虚拟环境路径
            venv_path = os.path.abspath(f"../../../venvs/{virtualenv_name}/Scripts/activate.bat")
            test_script = os.path.abspath(test_file)

            # 使用虚拟环境中的 Python 解释器运行测试
            command = f'cmd /c "{venv_path} && python {test_script}"'

            # 运行测试并捕获输出
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
            output = result.stdout + (result.stderr if result.stderr is not None else '')
            # print(f"Running tests in {sub_dir}...\nOutput:\n{output}")
            print("*" * 50 + f"Running tests in {sub_dir}" + "*" * 50)

            # 解析输出并更新对应的JSON数据
            parse_and_update_json(task_dir, sub_dir, output, json_file)


def parse_and_update_json(task_id, sub_dir, test_output, json_file):
    # 使用正则表达式匹配总的测试用例数量
    total_pattern = r'Ran (\d+) tests'
    total_tests_match = re.search(total_pattern, test_output)
    total_tests = int(total_tests_match.group(1)) if total_tests_match else 0

    # 使用正则表达式匹配失败的测试用例及其错误信息
    # failed_pattern = r'FAIL: (test_.+?) \(.+?\)\n-+\n(.+?)(?=\n\n|Ran)'  # 正则匹配模式错误
    failed_pattern = r'={70}\n(?:FAIL): (test_.+?) \(.+?\)\n(.+?)(?=\n\n)'
    failed_tests = re.findall(failed_pattern, test_output, re.DOTALL)

    # 使用正则表达式匹配错误的测试用例及其错误信息
    # error_pattern = r'ERROR: (test_.+?) \(.+?\)\n-+\n(.+?)(?=\n\n|Ran)'  # 正则匹配模式错误
    error_pattern = r'={70}\n(?:ERROR): (test_.+?) \(.+?\)\n(.+?)(?=\n\n)'
    error_tests = re.findall(error_pattern, test_output, re.DOTALL)
    # print(error_tests)

    # 统计失败和错误的数量
    num_failed_tests = len(failed_tests)
    num_error_tests = len(error_tests)

    # 提取通过的数量：OK表示全部通过，其他情况下通过数=总数 - (失败数 + 错误数)
    passed_tests = total_tests - len(failed_tests) - len(error_tests)

    # 计算通过率，保留两位小数
    pass_rate = round((passed_tests / total_tests), 2) if total_tests > 0 else 0

    with open(json_file, 'r+', encoding='utf-8') as file:
        data = json.load(file)

        for item in data['data']:
            if item['id'] == task_id:  # 匹配 task_id

                # 初始化 test_results 字典，如果还不存在
                if 'test_results' not in item:
                    item['test_results'] = {}

                # 获取子目录的索引部分（例如 task_id_1 中的 1）
                sub_dir_index = sub_dir.split('_')[-1]

                # 如果没有测试运行，记录错误信息并标记为 "未运行"
                if total_tests == 0:
                    item['test_results'][sub_dir_index] = {
                        "num_passed_tests": 0,
                        "total": 0,
                        "pass_rate": 0,
                        "num_failed_tests": 0,
                        "num_error_tests": 0,
                        "failed_tests": [],
                        "error_tests": [],
                        "error": "Test did not run, likely due to an import or setup issue.",
                        "output": test_output.strip()  # 捕获完整的错误输出
                    }
                else:
                    # 更新测试结果，记录通过的测试、失败的测试和错误的测试信息
                    item['test_results'][sub_dir_index] = {
                        "num_passed_tests": passed_tests,
                        "total": total_tests,
                        "pass_rate": pass_rate,  # 添加通过率，保留两位小数
                        "num_failed_tests": num_failed_tests,  # 记录失败的个数
                        "num_error_tests": num_error_tests,  # 记录错误的个数
                        "failed_tests": [{"test": test, "error": error.strip()} for test, error in failed_tests],
                        "error_tests": [{"test": test, "error": error.strip()} for test, error in error_tests],
                        "error": '',
                        "output": test_output.strip()  # 捕获完整的测试输出，方便排查
                    }
                break

        # 写回文件
        file.seek(0)
        json.dump(data, file, indent=4, ensure_ascii=False)
        file.truncate()


if __name__ == '__main__':
    # model_name = 'Llama-3-70B'
    # index = '1'
    # task = 'block'
    # testing_directory = f'../testing_pass@k_{model_name}_{index}_{task}_without_import'  # 填写测试目录的路径
    # json_file = f'../../../output_granularity_data/filter_with_info_v3/{model_name}/{index}/test_data_{task}_without_import.json'  # 填写json文件的路径
    # run_tests(testing_directory, json_file)

    # auto
    model_names = ['GPT-3.5', 'GPT-4o', 'Llama-3-70B']
    tasks = ['token', 'line', 'block']  # 定义三种不同的任务
    index = '1'

    for model_name in model_names:
        for task in tasks:
            print("【" * 50 + f"Testing for model {model_name} on task {task}" + "】" * 50)
            testing_directory = f'../testing_pass@k_{model_name}_{index}_{task}_with_complete_import'
            json_file = f'../../../output_granularity_data/filter_with_info_v3/{model_name}/{index}/test_data_{task}_with_complete_import.json'
            run_tests(testing_directory, json_file)
