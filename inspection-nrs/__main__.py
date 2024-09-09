from typing import List
from tqdm import tqdm
import os


def bootstrap_inspection_nrs(file: str) -> List[str]:
    with open(file, 'r', encoding='utf-8') as f:
        lines: List[str] = f.readlines()
    return [line.split(': ')[-1] for line in lines]

def save2file(file: str, context: List[str]) -> None:
    with open(file, 'w', encoding='utf-8') as f:
        f.writelines(context)
    return None

def main() -> None:
    lines: List[str] = []
    for file in tqdm(os.listdir('./')):
        file_path = os.path.join('./', file)
        if os.path.isfile(file_path):  # Only process files, not directories
            lines.extend(bootstrap_inspection_nrs(file_path))
    save2file("./Inspection Nrs.txt", lines)

# Main
if __name__ == '__main__':
    main()
