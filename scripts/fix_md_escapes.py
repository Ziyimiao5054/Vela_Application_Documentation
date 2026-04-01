import os
import re
from pathlib import Path

def fix_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 将文本按照多行代码块和单行代码块进行切分
    # 奇数索引一定是代码块内部（```...``` 或 `...`）
    parts = re.split(r"(```[\s\S]*?```|`[^`]*`)", content)
    changed = False
    
    for i in range(len(parts)):
        if i % 2 == 1:
            # 仅在代码块内部安全地进行还原，防止破坏 MDX 渲染引擎（MDX视非反引号中的 < 为 JSX 组件）
            original = parts[i]
            parts[i] = parts[i].replace("&lt;", "<").replace("&gt;", ">")
            parts[i] = parts[i].replace("&#123;", "{").replace("&#125;", "}")
            if original != parts[i]:
                changed = True
                
    if changed:
        new_content = "".join(parts)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed escapes in: {file_path}")

def main():
    # 自动遍历 docs-quickapp 目录下的所有 markdown 文件
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
            
    print(f"\nDone! Processed markdown files.")

if __name__ == "__main__":
    main()
