"""
测试llama3-70B的bock
"""
import json
from together import Together
import time
import tiktoken
from rdflib import Graph
import os

# encoding = tiktoken.get_encoding("gpt2")

test_file_dir = "../../ datasets/code_migration/samples"


def load_json(input_file):
    """加载 JSON 文件并返回数据"""
    with open(input_file, "r") as f:
        load_dict = json.load(f)
        try:
            load_data = load_dict["data"]
        except Exception as e:
            print(e)
            print(input_file)
    return load_data


def get_inner_kg(package, version):
    file_path = f"../kg_data/N_Quads/{package}/{package}{version}.nq"
    res = load_kg(file_path)
    return res


def get_inter_kg(package, old_version, new_version):
    file_path = f"../kg_data/N_Quads/{package}/changes/{old_version}_{new_version}_changes.nq"
    res = load_kg(file_path)
    return res


def load_kg(file_path):
    # 创建一个 RDF 图
    graph = Graph()

    # 加载 .nq 文件
    graph.parse(file_path, format="nquads")

    # 提取前三个三元组（忽略 graph）
    triples = []
    for subject, predicate, obj, _ in graph.triples((None, None, None)):
        triples.append((subject, predicate, obj))
    return triples


def truncate_text(text, max_tokens):
    # 获取GPT-3.5或GPT-4的分词器
    encoding = tiktoken.get_encoding("gpt2")
    disallowed_special = ()

    # 将文本编码为tokens
    tokens = encoding.encode(text, disallowed_special=disallowed_special)
    print(len(tokens))

    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]

    # 将截断的tokens解码为文本
    truncated_text = encoding.decode(tokens)

    return truncated_text


def predict(text: str, model_name: str):
    """
    获取困惑度
    :param text:
    :return:
    """
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": text}],
        frequency_penalty=0.1,
        max_tokens=512,
        logit_bias=None,
        logprobs=None,
        n=6,
        presence_penalty=0.0,
        stop=None,
        stream=False,
        temperature=0.8,
        top_p=0.95
    )
    # content = response
    # content1 = response.choices
    choices_list = response.choices

    ans_list = []
    for c in choices_list:
        content = c.message.content
        # if "," in content:
        #     content = content.split(',')[0]
        ans_list.append(content)
    final_ans = str(ans_list)

    return final_ans


def bulid_prompt_plan(old_version, new_version, old_code_snippet, old_knowledge_graph, new_knowledge_graph,
                      api_change_graph) -> str:
    """
    构建prompt
    :param version:
    :param description:
    :param masked_code:
    :param options:
    :return:
    """
    prompt_plan = (
        f"""

        ### Task
        You need to select some paths from the provided old version number, new version number, old version code snippet, the knowledge graphs of both versions and a knowledge graph recording the evolution across two versions that will be helpful for the subsequent code migration task. \n
        This process is called planning.
        In the planning phase, you need to select some paths from the provided knowledge graphs that will be helpful for the subsequent code migration task. These paths should clearly reflect the API changes between the two versions and provide guidance for the code migration.\n
        By analyzing the knowledge graphs of both versions, identify paths related to the old version code snippet and provide guidance for the subsequent code migration task. You can overlook the prefix of entities and relations for betther understanding.


        ### Context
        You will receive:\n
        - Old version: {old_version}
        - New version: {new_version}
        - Old code snippet to be migrated: {old_code_snippet}
        - Knowledge graph of the old version: {old_knowledge_graph}
        - Knowledge graph of the new version: {new_knowledge_graph}
        - Knowledge graph of API changes between the two versions: {api_change_graph}



        ### Output
        Please return a dictionary containing the following and omit any explanations or extra information\n\n":
        1. `selected_paths`: A list of selected paths from the three knowledge graphs.

        Your response:
        """
    )

    return prompt_plan


def bulid_prompt_reason(old_version, new_version, old_code_snippet, masked_code, selected_paths) -> str:
    """

    :param old_version:
    :param new_version:
    :param old_code_snippet:
    :param old_knowledge_graph:
    :param new_knowledge_graph:
    :param selected_paths:
    :return:
    """
    prompt_reason = (
        f"""
    Task Description:
    In the planning phase, you have selected paths from the knowledge graphs that are related to the old version code snippet. \n
    Now, you need to use these paths to generate code that is compatible with the new version APIs. This process is called reasoning.
    Objective:
    By analyzing the paths selected in the planning phase, generate a code snippet that is compatible with the new version API while ensuring that the functionality and semantics remain consistent with the old version.

    Input:
    1. Old version number: {old_version}
    2. New version number: {new_version}
    3. Old version code snippet: {old_code_snippet}
    4. Selected paths from the planning phase: {selected_paths}
    5. Target Code Snippet with <block_mask>:\n{masked_code}\n\n"

    Output:
    1. Code snippet compatible with the new version API.

    Provide your response as follows:\n"
    "   - Return only the code that fills the <block_mask> to complete the function for the target library version\n"
    "   - Enclose your code with <start> <end> to denote it as a Python code block\n"
    "   - Omit any explanations or extra information\n\n"
    Your response:
    """
    )

    return prompt_reason


def safe_predict(prompt, model_name, max_retries=10000, delay=10):
    for _ in range(max_retries):
        try:
            return predict(prompt, model_name)
        except Exception as e:
            print(f"错误：{e}。{delay} 秒后重试...")
            time.sleep(delay)
    print("达到最大重试次数。无法处理此项。")
    return None


if __name__ == "__main__":

    max_tokens = 8000  # llama3-8b窗口8k
    client = Together(api_key='159c9dc94810155413c9c4c7b2022eb232fc90e0d8f781d382604d029fd51b4b')
    model_name = "deepseek-ai/DeepSeek-V3"
    test_file_dir = "../../datasets/code_migration/samples"
    model_name_file = model_name.split("/")[-1]
    output_dir = os.path.join(test_file_dir, "outputs", model_name_file)
    index = 'all'

    # 改这
    edit_order = 'minor_to_major'
    # old_to_new, new_to_old, major_to_major, major_to_minor, minor_to_minor, minor_to_major


    original = 'old'  # migration参考的库版本
    target = 'new'  # 目标库版本
    if edit_order == 'new_to_old':
        original = 'new'
        target = 'old'
    if "new" in edit_order:
        file_name = f'code_migration_exe_{edit_order}.json'
    else:
        file_name = f'{edit_order}.json'
    input_file_path = os.path.join(test_file_dir, file_name)

    with open(input_file_path, 'r', encoding='utf-8') as fr:
        lodict = json.load(fr)
    data_dict = lodict

    #   逐条预测

    for data in data_dict['data']:
        if "model_output" in data:
            print(f"第{data_dict['data'].index(data) + 1}条已经预测过，跳过该数据！")
            continue

        print(f"正在预测第{data_dict['data'].index(data) + 1}条")
        dependency = data['dependency']

        # without dependency
        old_version = data[f'{original}_version']

        new_version = data[f'{target}_version']

        original_version = data['dependency'] + data[f'{original}_version']
        target_version = data['dependency'] + data[f'{target}_version']

        # original_code = data[f'{original}_task_function']
        # masked_code = data[f'masked_{target}_task_function']

        try:
            old_kg = get_inner_kg(dependency, old_version)
            new_kg = get_inner_kg(dependency, new_version)
            evol_kg = get_inter_kg(dependency, old_version, new_version)
        except Exception as e:
            print(f"Error: {e}")

        pass