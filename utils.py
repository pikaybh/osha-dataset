from bs4 import BeautifulSoup
from typing import List, Dict
import logging
import requests
import argparse

# Parser
parser = argparse.ArgumentParser(description='Extract Summary Nrs from an HTML file')
parser.add_argument('--file', '-F', type=str, help='Path to the HTML file')  # , required=True)
args = parser.parse_args()

# Root 
logger_name = 'utils'
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


def get_report_id(html: str) -> List[str]:
    # 파일을 텍스트 모드로 열어서 전체 내용을 하나의 문자열로 읽어오기
    with open(html, 'r', encoding="utf-8") as file:
        html_content = file.read()  # file.readlines() 대신 file.read() 사용
    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, 'html.parser')
    # 'Results Table'이라는 aria-label을 가진 테이블 찾기
    results_table = soup.find('table', {'aria-label': ''})
    logger.debug(f"{results_table = }")
    if results_table is None:
        logger.error("Error: Table not found in the provided HTML.")
        return
    # 'Report ID' 헤더를 찾기
    report_id_index = None
    for index, th in enumerate(results_table.find_all('th')):
        logger.debug(f"{th = }")
        if th.text.strip() == 'Summary Nr':
            report_id_index = index
            break
    if report_id_index is None:
        logger.error("Error: 'Summary Nr' column not found.")
        return
    # 모든 'Report ID' 아래의 id들을 추출
    report_ids = []
    for row in results_table.find('tbody').find_all('tr'):
        columns = row.find_all('td')
        if len(columns) > report_id_index:
            report_id = columns[report_id_index].text.strip()
            report_ids.append(report_id)
    # 결과 출력
    logger.debug(report_ids)
    return report_ids
# 텍스트 파일에서 ID 목록을 읽어옵니다.
def read_ids_from_file(file_path: str) -> List[str]:
    with open(file_path, 'r') as file:
        ids = file.read().splitlines()
    return ids
# 주어진 ID를 사용하여 웹사이트에서 'Inspection Nr'을 가져옵니다.
def fetch_inspection_nr(id: str) -> str:
    url: str = f"https://www.osha.gov/ords/imis/accidentsearch.accident_detail?id={id}"
    headers: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    response = requests.get(url, headers=headers)
    logger.info(f"{response = }")
    if response.status_code == 200:
        logger.info(dir(response))
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'name': 'accidentOverview'})
        logger.info(f"{table = }")
        if table:
            # 테이블의 모든 행을 순회하며 "Inspection Nr"을 찾습니다.
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) > 1 and "Inspection Nr" in cells[0].text:
                    return cells[1].text.strip()
    else:
        logger.error(f"Error occurred for ID: {id} with status code: {response.status_code}\n{response.headers = }\n{response.text = }")
    return None

def main() -> None:
    get_report_id(args.file)

# Main
if __name__ == '__main__':
    main()
