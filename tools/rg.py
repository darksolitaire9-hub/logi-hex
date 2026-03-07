import os

needle = "sqlite_repo"
root = "."

for dirpath, _, filenames in os.walk(root):
    for name in filenames:
        if not name.endswith(".py"):
            continue
        path = os.path.join(dirpath, name)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        if needle in text:
            print(f"{path}: contains '{needle}'")
