# Internal Modules
from utils import get_report_id
# External Modules
from tqdm import tqdm
from typing import List
import argparse
import logging
import os


parser = argparse.ArgumentParser(description='Extract Summary Nrs from the HTML files')
parser.add_argument('--directory', '-D', default="./", type=str, help='Path to folder where the HTML are stored')  # , required=True)
args = parser.parse_args()

# Root 
logger_name = 'summary'
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)
# File Handler
file_handler = logging.FileHandler(f'logs/{logger_name}.log', encoding='utf-8-sig')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(r'%(asctime)s [%(name)s, line %(lineno)d] %(levelname)s: %(message)s'))
logger.addHandler(file_handler)
# Stream Handler
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(r'%(message)s'))
logger.addHandler(stream_handler)


def get_htmls(folder: str) -> List[str]:
    return [file for file in os.listdir(folder) if file.endswith('.html') and not file.endswith('(tmp).html')]

def main() -> None:
    summary_nrs : List[str] = []
    for html in tqdm(get_htmls(args.directory)):
        summary_nrs.extend(get_report_id(html))  # 리스트를 평탄화하여 추가
    with open("Summary_Nrs.txt", 'w', encoding="utf-8") as file:
        file.writelines(f"{nr}\n" for nr in summary_nrs)  # 각 항목을 줄 바꿈과 함께 기록

# Main
if __name__ == '__main__':
    main()
