import os
import re
from pathlib import Path

def fix_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 修复缺失空格的有序列表: 匹配行首可能包含空白、-*+符号以及**的情形，后面紧跟数字、点，可能含有**，然后紧接了一个不为空白也不为数字的字符
    # 替换时在点和该字符中间强行插入一个空格
    # (?m) 开启多行模式，^ 匹配行首
    pattern = re.compile(r"(?m)(^[\s\-\*\+]*?(?:\*\*)?\d+\.(?:\*\*)?)([^\s\d])")
    
    new_content = pattern.sub(r"\1 \2", content)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed lists in: {file_path}")

def main():
    target_dir = Path("docs-quickapp")
    if not target_dir.exists():
        print(f"Error: Directory '{target_dir}' not found.")
        return

    count = 0
    for md_file in target_dir.rglob("*.md"):
        try:
            fix_file(md_file)
            count += 1
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
            
    print(f"\nDone! Processed list formats.")

if __name__ == "__main__":
    main()
