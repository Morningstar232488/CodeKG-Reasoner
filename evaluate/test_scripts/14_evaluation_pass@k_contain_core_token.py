"""
pass@k指标，评估token级别的能力
"""

import json
import os
import math
import re


def compute_score_k_token(test_results:dict, k:int, core_token, model_output_clear):
    """
    根据给定的test_results字典计算pass@k分数。
    test_results中的每个键值对代表一个测试用例的结果，其中包含一个pass_rate键。
    仅当pass_rate等于1.0时，测试用例才算通过。

    Args:
    test_results (dict): 包含测试用例结果的字典。
    k (int): 通过的测试用例的最小数量。

    Returns:
    float: 计算得到的pass@k分数。
    """
    c = 0
    n = len(test_results)
    for key, value in test_results.items():
        # if value.get('pass_rate', 0) == 1.0 and core_token in model_output_clear[int(key)-1]:
        if value.get('pass_rate', 0) == 1.0 and re.search(rf'\b{re.escape(core_token)}\b', model_output_clear[int(key) - 1]):
            c += 1

    if n-c < k:
        return 1.0

    score = 1 - (math.comb(n - c, k))/(math.comb(n, k))

    return score

if __name__ == '__main__':
    # 只用于检测tok_without_versionen、line和block
    model_name = 'GPT-4o'
    index = 'final'
    task = 'block'
    k = 1
    result_path = f'../../../update_sklearn_error/filter_with_info_v3/{model_name}/{index}/test_data_{task}_without_import_without_version.json'

    with open(result_path, 'r', encoding='utf-8')as fr:
        lodict = json.load(fr)
    data = lodict

    data_list = data['data']
    score_list = []

    for d in data_list:
        test_results = d['test_results']
        # 设为n=6，截取字典的前6个元素
        test_results = {str(i): test_results[str(i)] for i in range(1, 7) if str(i) in test_results}

        core_token = d['core_token']

        # 设为n=6，[:6]
        model_output_clear = d['model_output_clear'][:6]

        temp_score = compute_score_k_token(test_results, k, core_token, model_output_clear)
        score_list.append(temp_score)

    final_score = sum(score_list)/len(score_list)

    print(final_score)
