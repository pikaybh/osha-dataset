from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import time
import os

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--incognito")  # 시크릿 모드로 시작
chrome_options.add_argument(f"--user-data-dir={os.path.join(os.getcwd(), 'chrome_user_data')}")  # 사용자 데이터 디렉토리 지정
chrome_options.add_argument("--no-first-run")  # 첫 실행 화면 무시
chrome_options.add_argument("--no-default-browser-check")  # 기본 브라우저 설정 무시
chrome_options.add_argument("--disable-extensions")  # 확장 프로그램 비활성화
chrome_options.add_argument("--start-maximized")  # 브라우저 창 최대화

# ChromeDriver 서비스 설정
service = Service(ChromeDriverManager().install())

# 브라우저를 열고 여러 ID로 웹사이트에 접속합니다.
def fetch_inspection_nrs(ids):
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 여러 ID를 &로 묶어서 하나의 URL로 만듭니다.
    ids_param = '&'.join([f"id={id}" for id in ids])
    url = f"https://www.osha.gov/ords/imis/accidentsearch.accident_detail?{ids_param}"
    driver.get(url)

    results = {}
    try:
        # 페이지가 완전히 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table[name='accidentOverview']"))
        )

        # 각 테이블에서 'Inspection Nr' 값을 추출합니다.
        tables = driver.find_elements(By.CSS_SELECTOR, "table[name='accidentOverview']")
        for i, table in enumerate(tables):
            inspection_nr_element = table.find_element(By.XPATH, ".//tr[2]/td[1]/a")
            inspection_nr = inspection_nr_element.text.strip()
            results[ids[i]] = inspection_nr

    except Exception as e:
        print(f"Error occurred for IDs: {ids}, {str(e)}")

    driver.quit()
    return results

# 텍스트 파일에서 ID 목록을 읽어옵니다.
def read_ids_from_file(file_path):
    with open(file_path, 'r') as file:
        ids = file.read().splitlines()
    return ids

# Inspection Nr을 파일에 저장합니다.
def save_inspection_nrs_to_file(results, output_file_path):
    with open(output_file_path, 'w') as file:
        for id, inspection_nr in results.items():
            file.write(f"{id}: {inspection_nr}\n")

# 메인 함수
def main(input_file_path):
    ids = read_ids_from_file(input_file_path)
    results = {}
    batch_size = 1_000
    group_size = 25  # 한 번에 10개씩 처리

    for i in tqdm(range(0, len(ids), batch_size)):
        batch_ids = ids[i:i + batch_size]

        for j in range(0, len(batch_ids), group_size):
            group_ids = batch_ids[j:j + group_size]
            group_results = fetch_inspection_nrs(group_ids)
            results.update(group_results)

            # 각 요청 사이에 지연 시간을 추가합니다.
            time.sleep(2)

        # 중간 결과 저장
        output_file_path = f"inspection-nrs/Inspection_Nrs({i}~{i + len(batch_ids)}).txt"
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        save_inspection_nrs_to_file(results, output_file_path)

        # 배치 완료 후 결과 초기화
        results = {}

# 파일 경로를 지정하고 함수를 호출합니다.
if __name__ == "__main__":
    input_file_path = "Summary_Nrs.txt"  # 입력 텍스트 파일의 경로를 입력하세요.
    main(input_file_path)
