import ast
import random
import copy
import pandas as pd
import re
import os
from typing import Tuple, Optional

from src.app.models.bug_classifier.training import config

random.seed(42)

# ---------- Expanded base samples ----------

dataset_python = [
    {"code": "def add(a, b):\n    return a + b\n", "label": "CLEAN"},
    {"code": "def length_of_list(lst):\n    return len(lst)\n", "label": "CLEAN"},
    {
        "code": "def sum_list(lst):\n    total = 0\n    for i in range(len(lst)):\n        total += lst[i]\n    return total\n",
        "label": "CLEAN"},
    {
        "code": "def find_max(arr):\n    max_val = arr[0]\n    for i in range(1, len(arr)):\n        if arr[i] > max_val:\n            max_val = arr[i]\n    return max_val\n",
        "label": "CLEAN"},
    {
        "code": "def reverse_string(s):\n    result = ''\n    for i in range(len(s)):\n        result = s[i] + result\n    return result\n",
        "label": "CLEAN"},
    {"code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n", "label": "CLEAN"},
    {"code": "def is_even(n):\n    return n % 2 == 0\n", "label": "CLEAN"},
    {
        "code": "def count_vowels(text):\n    vowels = 'aeiou'\n    count = 0\n    for char in text.lower():\n        if char in vowels:\n            count += 1\n    return count\n",
        "label": "CLEAN"},
    {
        "code": "def get_average(numbers):\n    if len(numbers) == 0:\n        return 0\n    return sum(numbers) / len(numbers)\n",
        "label": "CLEAN"},
    {
        "code": "def merge_lists(list1, list2):\n    result = []\n    for item in list1:\n        result.append(item)\n    for item in list2:\n        result.append(item)\n    return result\n",
        "label": "CLEAN"},
    {
        "code": "def binary_search(arr, target):\n    left = 0\n    right = len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n",
        "label": "CLEAN"},
    {
        "code": "def filter_positive(numbers):\n    result = []\n    for num in numbers:\n        if num > 0:\n            result.append(num)\n    return result\n",
        "label": "CLEAN"},
    {
        "code": "def string_contains(text, substring):\n    for i in range(len(text) - len(substring) + 1):\n        if text[i:i+len(substring)] == substring:\n            return True\n    return False\n",
        "label": "CLEAN"},
    {
        "code": "def remove_duplicates(lst):\n    seen = set()\n    result = []\n    for item in lst:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result\n",
        "label": "CLEAN"},
    {
        "code": "def matrix_sum(matrix):\n    total = 0\n    for row in matrix:\n        for val in row:\n            total += val\n    return total\n",
        "label": "CLEAN"},
]

dataset_java = [
    {"code": "public int add(int a, int b) {\n    return a + b;\n}\n", "label": "CLEAN"},
    {"code": "public int getListSize(List<Integer> list) {\n    return list.size();\n}\n", "label": "CLEAN"},
    {
        "code": "public int sumArray(int[] arr) {\n    int total = 0;\n    for (int i = 0; i < arr.length; i++) {\n        total += arr[i];\n    }\n    return total;\n}\n",
        "label": "CLEAN"},
    {
        "code": "public int findMax(int[] arr) {\n    int max = arr[0];\n    for (int i = 1; i < arr.length; i++) {\n        if (arr[i] > max) {\n            max = arr[i];\n        }\n    }\n    return max;\n}\n",
        "label": "CLEAN"},
    {
        "code": "public String reverseString(String s) {\n    String result = \"\";\n    for (int i = s.length() - 1; i >= 0; i--) {\n        result += s.charAt(i);\n    }\n    return result;\n}\n",
        "label": "CLEAN"},
    {
        "code": "public int factorial(int n) {\n    if (n <= 1) {\n        return 1;\n    }\n    return n * factorial(n - 1);\n}\n",
        "label": "CLEAN"},
    {"code": "public boolean isEven(int n) {\n    return n % 2 == 0;\n}\n", "label": "CLEAN"},
    {
        "code": "public int countVowels(String text) {\n    String vowels = \"aeiouAEIOU\";\n    int count = 0;\n    for (int i = 0; i < text.length(); i++) {\n        if (vowels.indexOf(text.charAt(i)) != -1) {\n            count++;\n        }\n    }\n    return count;\n}\n",
        "label": "CLEAN"},
    {
        "code": "public double getAverage(int[] numbers) {\n    if (numbers.length == 0) {\n        return 0.0;\n    }\n    int sum = 0;\n    for (int i = 0; i < numbers.length; i++) {\n        sum += numbers[i];\n    }\n    return (double) sum / numbers.length;\n}\n",
        "label": "CLEAN"},
    {
        "code": "public boolean contains(int[] arr, int target) {\n    for (int i = 0; i < arr.length; i++) {\n        if (arr[i] == target) {\n            return true;\n        }\n    }\n    return false;\n}\n",
        "label": "CLEAN"},
    {
        "code": "public int binarySearch(int[] arr, int target) {\n    int left = 0;\n    int right = arr.length - 1;\n    while (left <= right) {\n        int mid = (left + right) / 2;\n        if (arr[mid] == target) {\n            return mid;\n        } else if (arr[mid] < target) {\n            left = mid + 1;\n        } else {\n            right = mid - 1;\n        }\n    }\n    return -1;\n}\n",
        "label": "CLEAN"},
    {
        "code": "public int[] filterPositive(int[] numbers) {\n    int count = 0;\n    for (int i = 0; i < numbers.length; i++) {\n        if (numbers[i] > 0) {\n            count++;\n        }\n    }\n    int[] result = new int[count];\n    int index = 0;\n    for (int i = 0; i < numbers.length; i++) {\n        if (numbers[i] > 0) {\n            result[index++] = numbers[i];\n        }\n    }\n    return result;\n}\n",
        "label": "CLEAN"},
]


# ---------- Python AST-based variable renaming ----------

class RenameVariables(ast.NodeTransformer):
    def __init__(self):
        self.mapping = {}
        self.reserved = {'self', 'cls', 'True', 'False', 'None'}

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Load)):
            if node.id not in self.mapping and node.id not in self.reserved:
                self.mapping[node.id] = f"var_{node.id}_{random.randint(1, 99)}"
            if node.id in self.mapping:
                node.id = self.mapping[node.id]
        return node

    def visit_arg(self, node):
        if node.arg not in self.mapping and node.arg not in self.reserved:
            self.mapping[node.arg] = f"param_{node.arg}_{random.randint(1, 99)}"
        if node.arg in self.mapping:
            node.arg = self.mapping[node.arg]
        return node


def rename_python_variables(code: str) -> Optional[str]:
    try:
        tree = ast.parse(code)
        tree = RenameVariables().visit(tree)
        return ast.unparse(tree)
    except:
        return None


# ---------- Python bug injection ----------

def inject_python_bug(code: str) -> Tuple[Optional[str], Optional[str]]:
    """Inject a bug and return (modified_code, bug_label)"""

    # Try each bug type until one succeeds
    bug_types = ["NULL_POINTER", "OFF_BY_ONE", "INCORRECT_RETURN", "LOGIC_ERROR"]
    random.shuffle(bug_types)

    for bug_type in bug_types:
        original_code = code
        modified = False

        if bug_type == "NULL_POINTER":
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if 'def ' in line and '(' in line:
                    match = re.search(r'def \w+\(([^)]+)\)', line)
                    if match and match.group(1).strip():
                        params = [p.strip().split('=')[0].strip() for p in match.group(1).split(',')]
                        if params and params[0]:
                            indent = len(line) - len(line.lstrip())
                            lines.insert(i + 1, ' ' * (indent + 4) + f"{params[0]} = None")
                            code = '\n'.join(lines)
                            modified = True
                            break

        elif bug_type == "OFF_BY_ONE":  # OFF_BY_ONE
            if 'range(len(' in code:
                code = re.sub(r'range\(len\((\w+)\)\)', r'range(len(\1) - 1)', code, count=1)
                modified = True
            elif 'range(1, len(' in code:
                code = re.sub(r'range\(1, len\((\w+)\)\)', r'range(2, len(\1))', code, count=1)
                modified = True
            elif 'for i in range(' in code and ', len(' in code:
                code = re.sub(r'range\((\d+), len\((\w+)\)\)', r'range(\1, len(\2) - 1)', code, count=1)
                modified = True

        elif bug_type == "INCORRECT_RETURN":  # INCORRECT_RETURN
            if 'return True' in code:
                code = code.replace('return True', 'return False', 1)
                modified = True
            elif 'return False' in code:
                code = code.replace('return False', 'return True', 1)
                modified = True
            elif re.search(r'return [a-zA-Z_]\w+\s*$', code, re.MULTILINE):
                code = re.sub(r'return ([a-zA-Z_]\w+)\s*$', r'return 0', code, count=1, flags=re.MULTILINE)
                modified = True

        elif bug_type == "LOGIC_ERROR":  # LOGIC_ERROR
            if '+=' in code:
                code = code.replace('+=', '-=', 1)
                modified = True
            elif '> ' in code and '>=' not in code:
                code = code.replace('> ', '>= ', 1)
                modified = True
            elif '< ' in code and '<=' not in code:
                code = code.replace('< ', '<= ', 1)
                modified = True
            elif '==' in code:
                code = code.replace('==', '!=', 1)
                modified = True

        # Validate and return if successful
        if modified and code != original_code:
            try:
                ast.parse(code)
                return code, bug_type
            except SyntaxError:
                code = original_code  # Reset for next attempt

    return None, None


# ---------- Java bug injection ----------

def inject_java_bug(code: str) -> Tuple[Optional[str], Optional[str]]:
    """Inject a bug and return (modified_code, bug_label)"""

    # Try each bug type until one succeeds
    bug_types = ["NULL_POINTER", "OFF_BY_ONE", "INCORRECT_RETURN", "LOGIC_ERROR"]
    random.shuffle(bug_types)

    for bug_type in bug_types:
        original_code = code
        modified = False

        if bug_type == "NULL_POINTER":
            lines = code.split('\n')
            for i, line in enumerate(lines):
                match = re.search(r'(String|Integer|int\[\]|List<\w+>)\s+(\w+)\s*=', line)
                if match:
                    var_name = match.group(2)
                    lines.insert(i + 1, f"    {var_name} = null;")
                    code = '\n'.join(lines)
                    modified = True
                    break

        elif bug_type == "OFF_BY_ONE":
            if 'i < ' in code and '.length' in code:
                if random.random() < 0.5:
                    code = re.sub(r'i < (\w+)\.length', r'i < \1.length - 1', code, count=1)
                else:
                    code = re.sub(r'i < (\w+)\.length', r'i <= \1.length - 1', code, count=1)
                modified = True
            elif 'i = 1; i <' in code:
                code = re.sub(r'i = 1; i < ', r'i = 2; i < ', code, count=1)
                modified = True

        elif bug_type == "INCORRECT_RETURN":
            if 'return true' in code:
                code = code.replace('return true', 'return false', 1)
                modified = True
            elif 'return false' in code:
                code = code.replace('return false', 'return true', 1)
                modified = True
            elif re.search(r'return [a-zA-Z_]\w+;', code):
                code = re.sub(r'return ([a-zA-Z_]\w+);', r'return 0;', code, count=1)
                modified = True

        elif bug_type == "LOGIC_ERROR":
            if '+=' in code:
                code = code.replace('+=', '-=', 1)
                modified = True
            elif '> ' in code and '>=' not in code:
                code = code.replace('> ', '>= ', 1)
                modified = True
            elif '< ' in code and '<=' not in code:
                code = code.replace('< ', '<= ', 1)
                modified = True
            elif '==' in code:
                code = code.replace('==', '!=', 1)
                modified = True

        if modified and code != original_code:
            return code, bug_type

    return None, None


# ---------- Augment dataset ----------

def augment_dataset(dataset, language, target_size=1000):
    augmented = []
    bug_stats = {"CLEAN": 0, "NULL_POINTER": 0, "OFF_BY_ONE": 0, "INCORRECT_RETURN": 0, "LOGIC_ERROR": 0}

    while len(augmented) < target_size:
        sample = random.choice(dataset)
        new_sample = copy.deepcopy(sample)
        code = new_sample["code"]

        # 70% chance to inject a bug
        if random.random() < 0.7:
            bug_code, bug_label = None, None
            for _ in range(3):  # Try up to 3 times
                if language == "python":
                    bug_code, bug_label = inject_python_bug(code)
                else:
                    bug_code, bug_label = inject_java_bug(code)

                if bug_code is not None:
                    break

            if bug_code is not None and bug_label is not None:
                code = bug_code
                label = bug_label
            else:
                # Failed to inject bug, keep as clean
                if language == "python" and random.random() < 0.5:
                    renamed = rename_python_variables(code)
                    if renamed:
                        code = renamed
                label = "CLEAN"
        else:
            # Keep clean
            if language == "python" and random.random() < 0.5:
                renamed = rename_python_variables(code)
                if renamed:
                    code = renamed
            label = "CLEAN"

        new_sample["code"] = code
        new_sample["label"] = label
        new_sample["language"] = language
        augmented.append(new_sample)
        bug_stats[label] += 1

    # Print distribution
    total_bugs = sum(bug_stats[i] for i in ["NULL_POINTER", "OFF_BY_ONE", "INCORRECT_RETURN", "LOGIC_ERROR"])
    print(
        f"  Clean: {bug_stats['CLEAN']}, Bugs: {total_bugs} (Labels 1-4: {bug_stats['NULL_POINTER']}, {bug_stats['OFF_BY_ONE']}, {bug_stats['INCORRECT_RETURN']}, {bug_stats['LOGIC_ERROR']})")

    return augmented


def build_dataset_if_missing():
    if os.path.exists(config.DATASET_PATH):
        print(f"✓ Dataset already exists at {config.DATASET_PATH}")
    else:
        print("Generating Python dataset...")
        aug_python = augment_dataset(dataset_python, "python", target_size=1000)

        print("Generating Java dataset...")
        aug_java = augment_dataset(dataset_java, "java", target_size=1000)

        # Merge, shuffle, save
        full_dataset = aug_python + aug_java
        random.shuffle(full_dataset)

        df = pd.DataFrame(full_dataset)

        print("\n=== Dataset Statistics ===")
        print(f"Total samples: {len(full_dataset)}")
        print(f"\nLabel distribution:")
        print(df['label'].value_counts().sort_index())
        print(f"\nLanguage distribution:")
        print(df['language'].value_counts())
        print(f"\nLabel distribution by language:")
        print(df.groupby(['language', 'label']).size().unstack(fill_value=0))

        df.to_csv(config.DATASET_PATH, index=False)
        print(f"\n✓ Saved dataset to {config.DATASET_PATH}")