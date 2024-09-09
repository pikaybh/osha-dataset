# Internal Modules
from utils import read_ids_from_file, fetch_inspection_nr
# External Modules
from time import sleep
from random import uniform
from tqdm import tqdm
from typing import List
import argparse
import logging
import os


parser = argparse.ArgumentParser(description='files')
parser.add_argument('--file', '-F', type=str, default="Summary_Nrs.txt", help='Path to file')  # , required=True)
args = parser.parse_args()

# Root 
logger_name = 'inspection_bs4'
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

def main() -> None:
    ids = read_ids_from_file(args.file)
    results = {}
    
    for id in tqdm(ids):
        inspection_nr = fetch_inspection_nr(id)
        if inspection_nr:
            results[id] = inspection_nr
            logger.debug(f"ID: {id}, Inspection Nr: {inspection_nr}")
        else:
            logger.error(f"ID: {id}, Inspection Nr not found or error occurred")
        # 각 요청 사이에 랜덤한 지연을 추가합니다.
        sleep(uniform(1, 3))
    return results

# Main
if __name__ == '__main__':
    main()
