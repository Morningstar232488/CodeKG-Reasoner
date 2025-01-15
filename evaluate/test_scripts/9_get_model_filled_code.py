import json
import sys


def replace_masks_with_answers(json_file: str, granularity: str) -> None:
    """
    Load data from a JSON file, replace all <mask> in each 'masked_code' with the content of 'model_answer',
    save the modified code under 'model_result' key and then write back to the original JSON file.

    Args:
    json_file (str): Path to the JSON file containing the data.
    """
    # Load data from the JSON file
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Process each entry in the 'data' key
    for entry in data['data']:

        # # 单个生成结果
        # # Replace <mask> with the content of 'model_response'
        # modified_code = entry['masked_task_function'].replace(granularity, entry['model_output_clear'])
        # # Store the modified code in 'model_response' key
        # entry['model_filled_code'] = modified_code

        # 多个生成结果（列表）
        # Prepare a dictionary to store the modified code for each 'model_output_clear' element
        modified_code_dict = {}
        # Replace <mask> with each element in 'model_output_clear'
        for idx, output in enumerate(entry['model_output_clear'], start=1):
            if granularity == "<token_mask>" or granularity == "<line_mask>":
                # modified_code = entry['masked_task_function'].replace(granularity, output)
                modified_code = entry['masked_task_function_without_import'].replace(granularity, output)
                # Use '1', '2', '3', ... as keys for the dictionary
                modified_code_dict[str(idx)] = modified_code

            if granularity == "<block_mask>":
                # Split the 'output' into lines for handling multiple lines
                output_lines = output.split('\n')
                # Check if the first line of 'output' is indented
                if not output_lines[0].startswith('    '):
                    # Add indentation to each line if not already indented
                    output_lines = ['    ' + line for line in output_lines]
                modified_code = '\n'.join(output_lines)

                # Replace the granularity mask with 'modified_code'
                # First, find the line number where the granularity mask is located
                # lines = entry['masked_task_function'].split('\n')
                lines = entry['masked_task_function_without_import'].split('\n')
                for line_number, line in enumerate(lines):
                    if granularity in line:
                        # Replace the line with 'modified_code'
                        lines[line_number] = modified_code
                        break
                # Join the lines back into a single string
                modified_code_final = '\n'.join(lines)

                # Store the modified code in a dictionary under 'model_filled_code' key
                modified_code_dict[str(idx)] = modified_code_final

        # Store the modified code dictionary in 'model_filled_code' key
        if len(modified_code_dict)>10:
            print(len(modified_code_dict))
        entry['model_filled_code'] = modified_code_dict

    # Write the modified data back to the JSON file
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print("'get_model_filled_code.py' has done!")


model_name = 'Llama-3-70B'
# task = 'line'
# task = sys.argv[2]
task = 'block'
granularity = f'<{task}_mask>'
input_file_path = sys.argv[1]
# input_file_path = f'../../../output_granularity_data/filter_with_info_v3/{model_name}/without_import_without_version/test_data_{task}_without_import_without_version.json'
replace_masks_with_answers(input_file_path, granularity)

