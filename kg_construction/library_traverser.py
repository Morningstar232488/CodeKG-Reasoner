#! /usr/bin/python3

import queue
import inspect
import sys
import re
import types
import parso
from collections import OrderedDict


def ensure_consistent_order(data, ordered_keys):
    return OrderedDict((key, data.get(key)) for key in ordered_keys if key in data)


class MemberInfoExtractor:
    def extract_args_doc(self, doc):
        return {}

    def extract_returns_doc(self, doc):
        return None

    def extract_raise_doc(self, doc):
        return None

    def is_deprecated(self, name, member):
        return False


def conver_to_code(value):
    if value is None:
        return "None"
    supported_types = (int, float, bool, str)
    if type(value) in supported_types:
        return repr(value)
    elif type(value) in (list, tuple) and all(element is None or type(element) in supported_types for element in value):
        return repr(value)
    else:
        return "___complex_type___"


class MemberVisitor:
    def __init__(self, data_output_handler, inspector=inspect,
                 extractor=MemberInfoExtractor()):
        self._yield_item = data_output_handler
        self._is_deprecated = extractor.is_deprecated
        self._extract_args_doc = extractor.extract_args_doc
        self._extract_returns_doc = extractor.extract_returns_doc
        self._extract_raise_doc = extractor.extract_raise_doc
        self._inspect = inspector

    def _parse_basic_info(self, name, member):
        basic_info = {
            "_id": name,
            "doc": self._inspect.getdoc(member),
            "is_deprecated": self._is_deprecated(name, member),
            "source_code": self._get_source_code(member)  # Add source code here
        }
        keys_order = ["_id", "doc", "is_deprecated", "source_code"]
        return ensure_consistent_order(basic_info, keys_order)

    def _try_get_func_def(self, func):
        if not self._inspect.getsourcefile(func):
            return None
        else:
            source = self._inspect.getsource(func)
            tree = parso.parse(source)
            return next(tree.iter_funcdefs(), None)

    def _get_sig_string(self, func):
        func_def = self._try_get_func_def(func)
        if func_def:
            return "(%s)" % "".join(p.get_code() for p in func_def.get_params())
        else:
            sig = self._inspect.signature(func)
            return "(%s)" % ", ".join(
                name if p.default is inspect.Parameter.empty else "%s=%s" % (
                    name, conver_to_code(p.default))
                for name, p in sig.parameters.items()
            )

    def _get_source_code(self, member):
        """ 获取源代码并进行适当的处理 """
        try:
            source_code = self._inspect.getsource(member)
            return source_code.strip()
        except (OSError, TypeError):
            return "Source code not available"

    def _parse_function(self, name, member):
        doc = self._inspect.getdoc(member)
        arg_doc = self._extract_args_doc(doc)

        sig_str = self._get_sig_string(member)
        sig = self._inspect.signature(member)

        parameters = OrderedDict(
            (pname, OrderedDict([
                ("description", arg_doc.get(pname, None)),
                ("is_optional", p.default is not inspect.Parameter.empty)
            ])) for pname, p in sig.parameters.items()
        )

        function_data = {
            **dict(self._parse_basic_info(name, member)),
            "signature": sig_str,
            "parameters": parameters,
            "returns_doc": self._extract_returns_doc(doc),
            "raise_doc": self._extract_raise_doc(doc)
        }

        keys_order = [
            "_id", "doc", "is_deprecated", "source_code",
            "signature", "parameters",
            "returns_doc", "raise_doc"
        ]

        return ensure_consistent_order(function_data, keys_order)

    def _parse_attribute(self, name, member, class_member):
        return dict(self._parse_basic_info(name, member))

    def _visit_module(self, name, member):
        module_data = {
            **self._parse_basic_info(name, member),
            "type": "module"
        }
        keys_order = ["_id", "doc", "is_deprecated", "source_code", "type"]
        self._yield_item(ensure_consistent_order(module_data, keys_order))

    def _visit_class(self, name, member):
        member_functions = (
            {
                **dict(self._parse_function(".".join([name, func_name]), func)),
                "type": "member_function",
                "class": name
            }
            for func_name, func in inspect.getmembers(member, self._inspect.isfunction)
            if (not func_name.startswith("_") or re.match(r"__.*__$", func_name))
        )

        attributes = (
            {
                **self._parse_attribute(".".join([name, attr_name]), attr, member),
                "type": "field",
                "class": name,
            }
            for attr_name, attr in inspect.getmembers(member)
            if (isinstance(attr, property) and not attr_name.startswith("_"))
        )

        mf_name_list = OrderedDict()
        attr_name_list = OrderedDict()

        for mf in member_functions:
            # mf_keys_order = [
            #     "_id", "doc", "is_deprecated", "source_code", "signature",
            #     "parameters", "returns_doc", "raise_doc",
            #     "type", "class"
            # ]
            mf_keys_order = [
                "_id", "doc", "is_deprecated", "source_code", "signature",
                "parameters", "returns_doc", "raise_doc",
                "type", "class"
            ]
            mf_ordered = ensure_consistent_order(mf, mf_keys_order)
            mf_name_list[mf_ordered["_id"]] = mf_ordered["signature"]
            self._yield_item(mf_ordered)

        for attr in attributes:
            attr_keys_order = [
                "_id", "doc", "is_deprecated", "source_code", "type", "class"
            ]
            attr_ordered = ensure_consistent_order(attr, attr_keys_order)
            attr_name_list[attr_ordered["_id"]] = attr_ordered["doc"]
            self._yield_item(attr_ordered)

        # 获取模块信息
        module_name = inspect.getmodule(member).__name__

        class_data = {
            **dict(self._parse_basic_info(name, member)),
            "member_functions": mf_name_list,
            "attributes": attr_name_list,
            "type": "class",
            "module": module_name
        }

        class_keys_order = [
            "_id", "doc", "is_deprecated", "source_code",
            "member_functions", "attributes", "type", "module"
        ]

        self._yield_item(ensure_consistent_order(class_data, class_keys_order))

    def _visit_function(self, name, member):
        try:

            # 获取函数所在的模块
            module_name = inspect.getmodule(member).__name__

            function_data = {
                **dict(self._parse_function(name, member)),
                "type": "function",
                "module": module_name
            }

            func_keys_order = [
                "_id", "doc", "is_deprecated", "source_code",
                "signature", "parameters",
                "returns_doc", "raise_doc", "type", "module"
            ]

            self._yield_item(ensure_consistent_order(function_data, func_keys_order))
        except:
            pass

    def _visit_module_field(self, name, member):
        module_field_data = {
            "_id": name,
            "doc": self._inspect.getdoc(member),
            "is_deprecated": self._is_deprecated(name, member),
            "source_code": self._get_source_code(member),  # Add source code for module fields
            "type": "module_field",
            "module": name[:name.rfind(".")]
        }

        module_field_keys = [
            "_id", "doc", "is_deprecated", "source_code", "type", "module"
        ]

        self._yield_item(ensure_consistent_order(module_field_data, module_field_keys))

    def __call__(self, name, member):
        try:
            if inspect.isfunction(member):
                self._visit_function(name, member)
            elif inspect.isclass(member):
                self._visit_class(name, member)
            elif not inspect.ismodule(member):
                d_name = name.split(".")[-1]
                if not d_name.startswith("_"):
                    self._visit_module_field(name, member)
        except OSError:
            pass


def is_private_name(name):
    return name.startswith("_") and (
        not re.match(r"__.*__$", name))


def should_visit(prefix=""):
    def predicate(member):
        if inspect.ismodule(member):
            return member.__name__.startswith(prefix)
        elif inspect.isclass(member) and hasattr(member, "__module__"):
            return member.__module__.startswith(prefix)
        elif inspect.isfunction(member):
            return True
        return True

    return predicate


def should_skip_child(name, child):
    return is_private_name(name) or name in {"__base__", "__class__", "__builtins__"} or (
        inspect.ismodule(child) and child.__name__ in sys.builtin_module_names
    )


def traverse_module(root, visit, module_prefix=None, prefix_black_list=set()):
    members = queue.deque()
    members.append(root)
    visited = []
    lossed_amount = 0
    while members:
        print(len(members))
        member_name, member = members.popleft()
        if member_name in prefix_black_list:
            continue
        try:
            visited.append(member)
        except Exception as any_exp:
            pass

        visit(member_name, member)
        if not inspect.ismodule(member):
            continue
        try:
            children = sorted(
                inspect.getmembers(member, should_visit(prefix=module_prefix))
            )
            for name, child in children:
                if should_skip_child(name, child):
                    continue
                try:
                    if child not in visited:
                        members.append((".".join([member_name, name]), child))
                except Exception as any_exp:
                    lossed_amount += 1
                    print(member_name)
                    change_child = str(name) + " " + str(type(child))
                    print(type(change_child))
                    print(change_child)
                    continue

        except ImportError as err:
            sys.stderr.write(
                "Error expanding %s due to an import error\n" % member_name
            )
            sys.stderr.write(err.msg)
    print(f"[SUMMARY] Total members that could not be processed: {lossed_amount}")