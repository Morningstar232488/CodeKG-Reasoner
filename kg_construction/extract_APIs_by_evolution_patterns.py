import json
import ast
import re
import sys
import os
from pathlib import Path

"""
python extract_APIs_by_evolution_patterns.py imageio 1.5 1.6
"""


def extract_version(filename):
    """
    从文件名中提取版本号。
    例如，文件名为 "==1.5.json"，则提取 "1.5"。
    """
    match = re.search(r'==(\d+\.\d+)\.json', filename)
    if match:
        return match.group(1)
    return None


def load_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data['data']


def save_json(json_file, data):

    json_dir = Path(json_file).parent

    if not os.path.exists(json_dir):
        os.mkdir(json_dir)
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print("save successfully!")

# signature是一个表示函数参数信息的字符串

def parse_signature(signature):
    # 构造一个完整的函数定义代码
    code = f"def temp_function{signature}: pass"

    # 解析代码
    parsed_code = ast.parse(code)

    params = {}

    # 查找函数定义节点
    for node in ast.walk(parsed_code):
        if isinstance(node, ast.FunctionDef):
            # 遍历函数的参数
            num_args = len(node.args.args)  # 参数总数
            num_defaults = len(node.args.defaults)  # 默认值的数量

            for i, arg in enumerate(node.args.args):
                param_name = arg.arg
                annotation = arg.annotation

                # 类型注解处理
                annotation_str = ast.dump(annotation) if annotation else None

                # 处理默认值
                if i >= (num_args - num_defaults):  # 检查参数是否有默认值
                    default_index = i - (num_args - num_defaults)
                    default = node.args.defaults[default_index]
                    if isinstance(default, ast.Constant):
                        default_value = default.value
                    elif isinstance(default, ast.Name):
                        default_value = default.id
                    else:
                        default_value = None
                else:
                    default_value = None

                # 将参数及其默认值和类型注解添加到字典中
                params[param_name] = {
                    "default_value": default_value,
                    "annotation": annotation_str
                }

    return params


# Class的两种pattern
def find_removed_classes(old_data, new_data):
    # import ipdb
    # ipdb.set_trace()

    old_class_ids = {item['_id'] for item in old_data if item['type'] == 'class'}
    new_class_ids = {item['_id'] for item in new_data if item['type'] == 'class'}
    removed_classes = old_class_ids - new_class_ids
    return [{**item, 'pattern': 'class_removal'} for item in old_data if item['_id'] in removed_classes]


def find_added_classes(old_data, new_data):
    old_class_ids = {item['_id'] for item in old_data if item['type'] == 'class'}
    new_class_ids = {item['_id'] for item in new_data if item['type'] == 'class'}
    added_classes = new_class_ids - old_class_ids
    return [{**item, 'pattern': 'class_addition'} for item in new_data if item['_id'] in added_classes]


# Methods的几种类型
def find_removed_functions(old_data, new_data):
    function_types = {'function', 'member_function'}
    old_function_ids = {item['_id'] for item in old_data if item['type'] in function_types}
    new_function_ids = {item['_id'] for item in new_data if item['type'] in function_types}
    removed_function_ids = old_function_ids - new_function_ids
    return [{**item, 'pattern': 'method_removal'} for item in old_data if item['_id'] in removed_function_ids]


def find_added_functions(old_data, new_data):
    function_types = {'function', 'member_function'}
    old_function_ids = {item['_id'] for item in old_data if item['type'] in function_types}
    new_function_ids = {item['_id'] for item in new_data if item['type'] in function_types}
    added_functions = new_function_ids - old_function_ids
    return [{**item, 'pattern': 'method_addition'} for item in new_data if item['_id'] in added_functions]


# def find_relocated_functions(old_data,new_data):
#     function_types = {'function', 'member_function'}
#     old_function_ids = {item['_id'] for item in old_data if item['type'] in function_types}
#     new_function_ids = {item['_id'] for item in new_data if item['type'] in function_types}
#
#     reloc_entry = []
#     for entry1 in old_function_ids:
#         for entry2 in new_function_ids:
#             if entry1.split('.')[-1] == entry2.split('.')[-1] :
#                 reloc_entry.append((entry1,entry2))
#     import ipdb
#     ipdb.set_trace()
#     return [{**entry[0],**entry[1],'pattern':'method_relocate'} for entry in reloc_entry
#             if '.'.join(entry[0].split('.')[:-1]) != '.'.join(entry[1].split('.')[:-1])]


# parameters的几种关系
def find_removed_required_parameters(old_data, new_data):
    removed_required_params = []
    function_types = {'function', 'member_function'}
    # 遍历旧版本中的所有函数或成员函数
    for old_item in old_data:
        if old_item['type'] in function_types:
            old_params = old_item.get('parameters', {})
            # 找到新版本中对应的函数或成员函数
            new_item = next((item for item in new_data if item['_id'] == old_item['_id']), None)
            if new_item:
                new_params = new_item.get('parameters', {})
                # 用来存储已删除的必需参数
                removed_params = []
                # 检查每个旧参数是否是必需的且在新版本中不存在
                for param, details in old_params.items():
                    if not details.get('is_optional', False) and param not in new_params:
                        removed_params.append({
                            'parameter': param,
                            'description': details.get('description', 'No description available')
                        })
                # 如果有已删除的必需参数，则生成一条数据
                if removed_params:
                    updated_item_info = old_item.copy()
                    updated_item_info['removed_required_parameters'] = removed_params
                    updated_item_info['pattern'] = 'required_parameter_removal'
                    removed_required_params.append(updated_item_info)
    return removed_required_params


def find_added_required_parameters(old_data, new_data):
    added_required_params = []
    function_types = {'function', 'member_function'}
    # 遍历新版本中的所有函数或成员函数
    for new_item in new_data:
        if new_item['type'] in function_types:
            new_params = new_item.get('parameters', {})
            # 找到旧版本中对应的函数或成员函数
            old_item = next((item for item in old_data if item['_id'] == new_item['_id']), None)
            if old_item:
                old_params = old_item.get('parameters', {})
                # 用来存储新增的必需参数
                added_params = []
                # 检查每个新参数是否是必需的且在旧版本中不存在
                for param, details in new_params.items():
                    if not details.get('is_optional', False) and param not in old_params:
                        added_params.append({
                            'parameter': param,
                            'description': details.get('description', 'No description available')
                        })
                # 如果有新增的必需参数，则生成一条数据
                if added_params:
                    updated_item_info = new_item.copy()
                    updated_item_info['added_required_parameters'] = added_params
                    updated_item_info['pattern'] = 'required_parameter_addition'
                    added_required_params.append(updated_item_info)
    return added_required_params


def find_parameter_reordering(old_data, new_data):
    reordering_changes = []
    # Function or member_function types to be checked
    function_types = {'function', 'member_function'}
    # Build a dictionary for quick lookup by ID for new data
    new_functions = {item['_id']: item for item in new_data if item['type'] in function_types}
    # Iterate over old data to find functions
    for old_item in old_data:
        if old_item['type'] in function_types and old_item['_id'] in new_functions:
            new_item = new_functions[old_item['_id']]
            old_params = list(old_item['parameters'].keys())
            new_params = list(new_item['parameters'].keys())
            # Check if the parameters are reordered
            if old_params != new_params and sorted(old_params) == sorted(new_params):
                # Create a copy of the function's data to avoid altering original data
                updated_function_info = old_item.copy()
                updated_function_info['reordering_changes'] = {
                    'old_order': old_params,
                    'new_order': new_params
                }
                updated_function_info['pattern'] = 'parameter_reordering'
                reordering_changes.append(updated_function_info)
    return reordering_changes


def find_removed_optional_parameters(old_data, new_data):
    removed_optional_params = []
    function_types = {'function', 'member_function'}
    # 将旧版本和新版本的函数按 _id 索引
    old_functions = {item['_id']: item for item in old_data if item['type'] in function_types}
    new_functions = {item['_id']: item for item in new_data if item['type'] in function_types}
    for func_id, old_func in old_functions.items():
        if func_id in new_functions:
            old_params = old_func.get('parameters', {})
            new_params = new_functions[func_id].get('parameters', {})
            old_param_ids = set(old_params.keys())
            new_param_ids = set(new_params.keys())
            # 用来存储已删除的可选参数
            removed_params = []
            # 检查是否有旧版本的可选参数在新版本中被删除
            for param in old_param_ids - new_param_ids:
                if old_params[param]['is_optional']:
                    removed_params.append({
                        "parameter": param,
                        "description": old_params[param].get('description', 'No description available')
                    })
            # 如果有已删除的可选参数，则生成一条数据
            if removed_params:
                updated_func_info = old_func.copy()
                updated_func_info['removed_optional_parameters'] = removed_params
                updated_func_info['pattern'] = 'optional_parameter_removal'
                removed_optional_params.append(updated_func_info)
    return removed_optional_params


def find_added_optional_parameters(old_data, new_data):
    added_optional_params = []
    function_types = {'function', 'member_function'}
    # 将旧版本和新版本的函数按 _id 索引
    old_functions = {item['_id']: item for item in old_data if item['type'] in function_types}
    new_functions = {item['_id']: item for item in new_data if item['type'] in function_types}
    for func_id, new_func in new_functions.items():
        if func_id in old_functions:
            old_params = old_functions[func_id].get('parameters', {})
            new_params = new_func.get('parameters', {})
            old_param_ids = set(old_params.keys())
            new_param_ids = set(new_params.keys())
            # 用来存储新增的可选参数
            added_params = []
            # 检查是否有新版本中的可选参数在旧版本中不存在
            for param in new_param_ids - old_param_ids:
                if new_params[param]['is_optional']:
                    added_params.append({
                        "parameter": param,
                        "description": new_params[param].get('description', 'No description available')
                    })
            # 如果有新增的可选参数，则生成一条数据
            if added_params:
                updated_func_info = new_func.copy()
                updated_func_info['added_optional_parameters'] = added_params
                updated_func_info['pattern'] = 'optional_parameter_addition'
                added_optional_params.append(updated_func_info)
    return added_optional_params


def find_removed_default_values(old_data, new_data):
    removed_defaults = []
    function_types = {'function', 'member_function'}
    # 构建函数信息字典，包括 'function' 和 'member_function'
    old_functions = {item['_id']: item for item in old_data if item['type'] in function_types}
    new_functions = {item['_id']: item for item in new_data if item['type'] in function_types}
    # 遍历旧版本中的函数，比较默认值
    for func_id, old_func in old_functions.items():
        if func_id in new_functions:
            old_params = parse_signature(old_func['signature'])
            new_params = parse_signature(new_functions[func_id]['signature'])
            removed_params = []  # 用来存储所有移除默认值的参数信息
            for param, old_param_info in old_params.items():
                old_default = old_param_info['default_value']  # 提取旧参数的默认值
                new_param_info = new_params.get(param)
                new_default = new_param_info['default_value'] if new_param_info else None  # 提取新参数的默认值
                # 检查是否旧版本中有默认值，而新版本中没有
                if old_default is not None and new_default is None:
                    removed_params.append({
                        'parameter': param,
                        'old_default': old_default
                    })
            # 如果有移除默认值的参数，则生成一条数据
            if removed_params:
                updated_func_info = old_func.copy()
                updated_func_info['removed_default_values'] = removed_params
                updated_func_info['pattern'] = 'parameter_default_value_removal'
                removed_defaults.append(updated_func_info)
    return removed_defaults


def find_added_default_values(old_data, new_data):
    added_defaults = []
    function_types = {'function', 'member_function'}
    # 构建函数信息字典，包括 'function' 和 'member_function'
    old_functions = {item['_id']: item for item in old_data if item['type'] in function_types}
    new_functions = {item['_id']: item for item in new_data if item['type'] in function_types}
    # 遍历新版本中的函数，比较默认值
    for func_id, new_func in new_functions.items():
        if func_id in old_functions:
            old_params = parse_signature(old_functions[func_id]['signature'])
            new_params = parse_signature(new_func['signature'])
            added_params = []  # 用来存储所有添加默认值的参数信息
            for param, new_param_info in new_params.items():
                new_default = new_param_info['default_value']  # 提取新参数的默认值
                old_param_info = old_params.get(param)
                old_default = old_param_info['default_value'] if old_param_info else None  # 提取旧参数的默认值
                # 检查是否新版本中有默认值，而旧版本中没有
                if new_default is not None and old_default is None:
                    added_params.append({
                        'parameter': param,
                        'new_default': new_default
                    })
            # 如果有添加默认值的参数，则生成一条数据
            if added_params:
                updated_func_info = new_func.copy()
                updated_func_info['added_default_values'] = added_params
                updated_func_info['pattern'] = 'parameter_default_value_addition'
                added_defaults.append(updated_func_info)
    return added_defaults


def find_changed_default_values(old_data, new_data):
    changed_defaults = []
    function_types = {'function', 'member_function'}
    # 构建函数信息字典，包括 'function' 和 'member_function'
    old_functions = {item['_id']: item for item in old_data if item['type'] in function_types}
    new_functions = {item['_id']: item for item in new_data if item['type'] in function_types}
    # 遍历旧版本中的函数，比较默认值
    for func_id, old_func in old_functions.items():
        if func_id in new_functions:
            new_func = new_functions[func_id]
            old_params = parse_signature(old_func['signature'])
            new_params = parse_signature(new_func['signature'])
            # 获取共有参数，即两个版本中都存在的参数
            common_params = set(old_params.keys()) & set(new_params.keys())
            changed_params = []  # 用来存储所有发生默认值变化的参数
            for param in common_params:
                old_default = old_params[param]['default_value']  # 获取旧版本参数的默认值
                new_default = new_params[param]['default_value']  # 获取新版本参数的默认值

                if old_default != new_default:
                    # 如果默认值发生了变化，则记录这个变化
                    changed_params.append({
                        'parameter': param,
                        'old_default': old_default,
                        'new_default': new_default
                    })
            # 如果有任何参数的默认值发生了变化，则生成一条数据
            if changed_params:
                updated_func_info = new_func.copy()
                updated_func_info['default_value_changed'] = changed_params
                updated_func_info['pattern'] = 'parameter_default_value_change'
                changed_defaults.append(updated_func_info)
    return changed_defaults


# Field的两种pattern
def find_removed_fields(old_data, new_data):
    field_types = {'field', 'module_field'}
    old_fields = {item['_id']: item for item in old_data if item['type'] in field_types}
    new_fields = {item['_id']: item for item in new_data if item['type'] in field_types}
    removed_field_ids = set(old_fields.keys()) - set(new_fields.keys())
    return [{**item, 'pattern': 'field_removal'} for item in old_data if item['_id'] in removed_field_ids]


def find_added_fields(old_data, new_data):
    field_types = {'field', 'module_field'}
    old_fields = {item['_id']: item for item in old_data if item['type'] in field_types}
    new_fields = {item['_id']: item for item in new_data if item['type'] in field_types}
    added_field_ids = set(new_fields.keys()) - set(old_fields.keys())
    return [{**item, 'pattern': 'field_addition'} for item in new_data if item['_id'] in added_field_ids]


# code migration的数据可以通过比较具有相同docstring、相同调用路径、但有不同id（API名称）来获取


if __name__ == '__main__':

    package_name = sys.argv[1]
    old_version = sys.argv[2]
    new_version = sys.argv[3]

    # old_version = "==" + _old_version
    # new_version = "==" + _new_version

    # 载入 JSON 数据
    # old_version_json = '../result/Flask_APIs_1.0.1.json'
    old_version_json = f'../kg_data/parsed_data/json_data/{package_name}/{old_version}.json'

    # new_version_json = '../result/Flask_APIs_1.0.2.json'
    new_version_json = f'../kg_data/parsed_data/json_data/{package_name}/{new_version}.json'
    output_json = f'../kg_data/parsed_data/json_data/{package_name}/changes/{old_version}_{new_version}_changes.json'


    # old_version = extract_version(old_version_json)
    # new_version = extract_version(new_version_json)
    if not os.path.exists(old_version_json):
        print(f"{old_version_json} not exists!" )
        sys.exit()
    if not os.path.exists(new_version_json):
        print(f"{new_version_json} not exists!" )
        sys.exit()


    _old_data = load_json(old_version_json)
    _new_data = load_json(new_version_json)



    old_data = _old_data.values()
    new_data = _new_data.values()

    # old_data = [{**item, 'version': old_version} for item in _old_data.values()]
    # # 为 new_version_data 中的每条数据添加 version: new_version
    # new_data = [{**item, 'version': new_version} for item in _new_data.values()]

    # 调用功能函数
    removed_classes = find_removed_classes(old_data, new_data)
    added_classes = find_added_classes(old_data, new_data)

    removed_functions = find_removed_functions(old_data, new_data)
    added_functions = find_added_functions(old_data, new_data)
    # relocated_functions = find_relocated_functions(old_data,new_data)
    removed_required_parameters = find_removed_required_parameters(old_data, new_data)
    added_required_parameters = find_added_required_parameters(old_data, new_data)
    parameter_reordering = find_parameter_reordering(old_data, new_data)
    removed_optional_parameters = find_removed_optional_parameters(old_data, new_data)
    added_optional_parameters = find_added_optional_parameters(old_data, new_data)
    removed_default_values = find_removed_default_values(old_data, new_data)
    added_default_values = find_added_default_values(old_data, new_data)
    changed_default_values = find_changed_default_values(old_data, new_data)

    removed_fields = find_removed_fields(old_data, new_data)
    added_fields = find_added_fields(old_data, new_data)


    all_results = []

    all_results.extend(removed_classes)
    all_results.extend(added_classes)
    all_results.extend(removed_functions)
    all_results.extend(added_functions)
    # all_results.extend(relocated_functions)
    all_results.extend(removed_required_parameters)
    all_results.extend(added_required_parameters)
    all_results.extend(parameter_reordering)
    all_results.extend(removed_optional_parameters)
    all_results.extend(added_optional_parameters)
    all_results.extend(removed_default_values)
    all_results.extend(added_default_values)
    all_results.extend(changed_default_values)
    all_results.extend(removed_fields)
    all_results.extend(added_fields)

    save_json(output_json,{'count': len(all_results), 'data': all_results})