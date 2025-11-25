import os
import subprocess
import csv
from java_augmented_dataset import generate_general_java_snippets, generate_spring_boot_snippets
from pathlib import Path
from config import LANGUAGES, TARGET_SAMPLES, MAX_TOKEN_LENGTH, OUTPUT_CSV

BASE_DIR = "repos"
os.makedirs(BASE_DIR, exist_ok=True)

def build_dataset_if_missing(tokenizer, csv_path=OUTPUT_CSV):
    """
    Builds dataset.csv with code snippets if it doesn't exist yet.
    - Skips cloning repos that already exist.
    - Splits files into 512-token chunks for CodeBERT.
    """
    if os.path.exists(csv_path):
        print(f"{csv_path} already exists. Skipping dataset creation.")
        return

    def shallow_clone(url, dest):
        if not os.path.exists(dest):
            print(f"Cloning {url} → {dest}")
            subprocess.run(["git", "clone", "--depth=1", url, dest])
        else:
            print(f"Repo exists, skipping clone: {dest}")

    def file_to_chunks(path):
        try:
            code = path.read_text(errors="ignore")
        except:
            return []

        tokens = tokenizer(
            code,
            truncation=False,
            add_special_tokens=False,
            return_tensors="pt"
        )["input_ids"][0]

        chunks = []
        for i in range(0, len(tokens), MAX_TOKEN_LENGTH):
            token_slice = tokens[i:i+MAX_TOKEN_LENGTH]
            text = tokenizer.decode(token_slice)
            chunks.append(text)

        return chunks

    def collect_language_samples(language, cfg):
        print(f"Collecting samples for: {language}")
        collected = []
        extensions = set([e.lower() for e in cfg["extensions"]])
        repos = cfg["repos"]

        for repo_url in repos:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            repo_path = Path(BASE_DIR) / repo_name
            shallow_clone(repo_url, repo_path)

            for file in repo_path.rglob("*.*"):
                if file.suffix.lower() in extensions:
                    chunks = file_to_chunks(file)
                    for c in chunks:
                        collected.append((c, language))
                        if len(collected) >= TARGET_SAMPLES:
                            print(f"Reached {TARGET_SAMPLES} samples for {language}")
                            return collected

        print(f"Only collected {len(collected)} samples for {language}")
        return collected

    all_rows = []
    for language, cfg in LANGUAGES.items():
        samples = collect_language_samples(language, cfg)
        all_rows.extend(samples)
        #For java, append general snippets and spring snippets
        if language == "java":
            n_general = 1000
            n_spring = 300
            general_snippets = generate_general_java_snippets(n_general)
            spring_snippets = generate_spring_boot_snippets(n_spring)
            all_rows.extend(general_snippets)
            all_rows.extend(spring_snippets)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code_snippet", "label"])
        for text, label in all_rows:
            writer.writerow([text, label])

    print(f"Dataset saved to {csv_path} ({len(all_rows)} samples)")
