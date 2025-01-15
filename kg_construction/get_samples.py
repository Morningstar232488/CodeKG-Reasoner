import json
import os

filr_dir = "../datasets/code_migration/original"

check_path = "../kg_data/parsed_data/json_data"
check_path_nq = "../kg_data/N_Quads"
write_dir = "../datasets/code_migration/samples"
sum = 0

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

def write_json(output_file,data_dict):
    """

    :param output_file:
    :param data_dict: data,(dict)
    :return: None
    """
    with open(output_file,"w") as of:
        of.write(json.dumps(data_dict,indent=4))
    print(f"Write to {output_file}")


if __name__ == "__main__":
    for root,_,files in os.walk(filr_dir):
        for file in files:
            res_dict = []
            if file.endswith(".json"):
                file_path = os.path.join(root,file)
                data = load_json(file_path)
                for entry in data:
                    package = entry["dependency"]
                    if "new_to_old" in file:
                        original_version = entry["new_version"]
                        target_version = entry["old_version"]

                        original_name = entry["new_name"]
                        target_name = entry["old_name"]
                    else:
                        original_version = entry["old_version"]
                        target_version = entry["new_version"]

                        original_name = entry["old_name"]
                        target_name = entry["new_name"]

                    old_version_path = os.path.join(check_path,package,original_version+".json")
                    new_version_path = os.path.join(check_path,package,target_version+".json")

                    if os.path.exists(old_version_path) and os.path.exists(new_version_path):
                        old_version_dict_keys = load_json(old_version_path).keys()
                        new_version_dict_keys = load_json(new_version_path).keys()

                        change_path = os.path.join(check_path_nq,package,"changes",f"{original_version}_{target_version}_changes.nq")


                        if os.path.exists(change_path) and original_name in old_version_dict_keys and target_name in new_version_dict_keys :
                        # if original_name in old_version_dict_keys and target_name in new_version_dict_keys :
                            res_dict.append(entry)

                res = {"count":res_dict.__len__(),"data":res_dict}

                write_path = os.path.join(write_dir,file)
                write_json(write_path,res)

                sum+=res_dict.__len__()

    print(f"The number of samples {sum}")








