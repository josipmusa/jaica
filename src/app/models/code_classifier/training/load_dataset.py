import csv
import random

NUM_SAMPLES_PER_LANG = 250  # 6 languages * 250 ≈ 1500

languages = {
    "Python": [
        "def {func_name}({args}):\n    {body}",
        "for {var} in range({start}, {end}):\n    {body}",
        "class {class_name}:\n    def __init__(self, {args}):\n        {body}",
        "{var} = [{vals}]",
        "if {cond}:\n    {body}\nelse:\n    {body2}"
    ],
    "Java": [
        "public class {class_name} {{\n    public static void main(String[] args) {{\n        {body}\n    }}\n}}",
        "int {func_name}(int {arg1}, int {arg2}) {{ return {arg1} + {arg2}; }}",
        "for(int {i}=0; {i}<{n}; {i}++) {{ {body} }}",
        "{type} {var} = new {type}();",
        "if({cond}) {{ {body} }} else {{ {body2} }}"
    ],
    "SQL": [
        "SELECT {columns} FROM {table} WHERE {cond};",
        "INSERT INTO {table} ({columns}) VALUES ({values});",
        "UPDATE {table} SET {col} = {val} WHERE {cond};",
        "DELETE FROM {table} WHERE {cond};",
        "CREATE TABLE {table} ({schema});"
    ],
    "JavaScript": [
        "function {func_name}({args}) {{ {body} }}",
        "for(let {i}=0; {i}<{n}; {i}++) {{ {body} }}",
        "const {var} = {value};",
        "{var}.forEach(item => {{ {body} }});",
        "if({cond}) {{ {body} }} else {{ {body2} }}"
    ],
    "PHP": [
        "<?php function {func_name}({args}) {{ {body} }} ?>",
        "<?php for(${i}=0; ${i}<{n}; ${i}++) {{ {body} }} ?>",
        "<?php ${var} = {value}; ?>",
        "<?php if({cond}) {{ {body} }} else {{ {body2} }} ?>",
        "<?php echo {value}; ?>"
    ],
    "HTML": [
        "<html><body><h1>{text}</h1></body></html>",
        "<div class='{class}'>{text}</div>",
        "<a href='{url}'>{text}</a>",
        "<ul>{items}</ul>",
        "<p>{text}</p>"
    ]
}

def random_string(length=5):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=length))

def generate_snippet(template):
    snippet = template
    snippet = snippet.replace("{func_name}", random_string())
    snippet = snippet.replace("{args}", ", ".join([random_string() for _ in range(random.randint(1, 3))]))
    snippet = snippet.replace("{body}", "pass" if "Python" in template else "// code")
    snippet = snippet.replace("{body2}", "pass" if "Python" in template else "// else code")
    snippet = snippet.replace("{class_name}", random_string().capitalize())
    snippet = snippet.replace("{var}", random_string())
    snippet = snippet.replace("{i}", "i")
    snippet = snippet.replace("{n}", "10")
    snippet = snippet.replace("{columns}", "*")
    snippet = snippet.replace("{table}", "my_table")
    snippet = snippet.replace("{cond}", "1=1")
    snippet = snippet.replace("{vals}", "1,2,3")
    snippet = snippet.replace("{type}", "MyType")
    snippet = snippet.replace("{value}", "42")
    snippet = snippet.replace("{text}", "Hello World")
    snippet = snippet.replace("{url}", "https://example.com")
    snippet = snippet.replace("{class}", "container")
    snippet = snippet.replace("{schema}", "id INT, name VARCHAR(50)")
    return snippet

# Build dataset
dataset = []
for lang, templates in languages.items():
    for _ in range(NUM_SAMPLES_PER_LANG):
        template = random.choice(templates)
        snippet = generate_snippet(template)
        dataset.append((snippet, lang))

# Shuffle dataset
random.shuffle(dataset)

# Save CSV
with open("code_type_dataset_full.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["code_snippet", "label"])
    writer.writerows(dataset)

print("Full dataset created: code_type_dataset_full.csv")
