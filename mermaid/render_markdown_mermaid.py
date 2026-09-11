import sys
import os
import glob
import re
import subprocess
import hashlib
import tempfile

sys.stdout.reconfigure(encoding='utf-8')

def process_markdown(md_path):
    if not os.path.exists(md_path):
        print(f"Error: File not found: {md_path}")
        return

    md_dir = os.path.dirname(os.path.abspath(md_path))
    images_dir = os.path.join(md_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)
    matches = list(pattern.finditer(content))

    if not matches:
        print(f"No unrendered mermaid blocks found in {os.path.basename(md_path)} (all already rendered or none present).")
        return

    print(f"Found {len(matches)} mermaid block(s) in {os.path.basename(md_path)}")

    new_content = content
    offset = 0

    for i, m in enumerate(matches):
        mmd_code = m.group(1).strip()
        code_hash = hashlib.md5(mmd_code.encode("utf-8")).hexdigest()[:8]
        img_name = f"mermaid_diagram_{i+1}_{code_hash}.png"
        img_path = os.path.join(images_dir, img_name)

        with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False, encoding="utf-8") as tf:
            tf.write(mmd_code)
            temp_mmd = tf.name

        try:
            cmd = ["C:\\tools\\mmdc.cmd", "-i", temp_mmd, "-o", img_path, "-b", "white", "-s", "2"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"  [OK] Compiled diagram {i+1} -> images/{img_name}")
                replacement = f"![Mermaid Diagram {i+1}](./images/{img_name})"
                start, end = m.span()
                start += offset
                end += offset
                new_content = new_content[:start] + replacement + new_content[end:]
                offset += len(replacement) - (m.end() - m.start())
            else:
                print(f"  [!] Failed to compile diagram {i+1}: {res.stderr}")
        finally:
            if os.path.exists(temp_mmd):
                os.remove(temp_mmd)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[OK] Successfully updated {os.path.basename(md_path)} with rendered images!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Auto-detect all markdown files in current working directory
        md_files = glob.glob("*.md")
        if not md_files:
            print("No .md files found in the current directory.")
            print("Usage: md-mermaid [optional-path-to-markdown-file]")
            sys.exit(0)
        print(f"Processing all Markdown files in current folder ({len(md_files)} found)...")
        for f in md_files:
            process_markdown(f)
    else:
        target = sys.argv[1]
        if os.path.isdir(target):
            for f in glob.glob(os.path.join(target, "*.md")):
                process_markdown(f)
        else:
            process_markdown(target)
