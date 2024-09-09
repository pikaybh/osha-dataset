from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
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

# 브라우저를 열고 Summary Nr에서 Inspection Nr를 추출합니다.
def fetch_inspection_nr(summary_nr):
    driver = webdriver.Chrome(service=service, options=chrome_options)
    url = f"https://www.osha.gov/ords/imis/accidentsearch.accident_detail?id={summary_nr}"
    driver.get(url)

    try:
        # 페이지가 완전히 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table[name='accidentOverview']"))
        )

        # 'accidentOverview' 테이블에서 'Inspection Nr' 값을 추출합니다.
        table = driver.find_element(By.CSS_SELECTOR, "table[name='accidentOverview']")
        inspection_nr_element = table.find_element(By.XPATH, ".//tr[2]/td[1]/a")
        inspection_nr = inspection_nr_element.text.strip()

        driver.quit()
        return inspection_nr

    except Exception as e:
        print(f"Error occurred for Summary Nr: {summary_nr}, {str(e)}")
        driver.quit()
        return None

# 브라우저를 열고 Inspection Detail 페이지에서 정보를 크롤링합니다.
def fetch_inspection_details(inspection_nr):
    driver = webdriver.Chrome(service=service, options=chrome_options)
    url = f"https://www.osha.gov/ords/imis/establishment.inspection_detail?id={inspection_nr}"
    driver.get(url)

    try:
        # 페이지가 완전히 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.row-fluid"))
        )

        data = {}

        # Inspection Nr, Report ID, Date Opened, Case Status 등 주요 정보를 추출합니다.
        inspection_info = driver.find_element(By.XPATH, "//h4").text
        case_status = driver.find_element(By.XPATH, "//div[@class='well well-small']").text
        inspection_nr_div = driver.find_element(By.XPATH, "//div[@class='span4'][strong[text()='Inspection Nr']]").text
        report_id_div = driver.find_element(By.XPATH, "//div[@class='span4'][strong[text()='Report ID']]").text
        date_opened_div = driver.find_element(By.XPATH, "//div[@class='span4'][strong[text()='Date Opened']]").text

        data['Inspection Nr'] = inspection_nr_div.split(": ")[1]
        data['Report ID'] = report_id_div.split(": ")[1]
        data['Date Opened'] = date_opened_div.split(": ")[1]
        data['Case Status'] = case_status.split(": ")[1]

        # Site Address, Mailing Address, Union Status, SIC, NAICS 정보 추출
        site_address = driver.find_element(By.XPATH, "//p[strong[text()='Site Address']]").text.replace("\n", ", ")
        mailing_address = driver.find_element(By.XPATH, "//p[strong[text()='Mailing Address']]").text.replace("\n", ", ")
        union_status = driver.find_element(By.XPATH, "//div[@class='span4'][p[strong[text()='Union Status']]]").text.split(": ")[1]
        naics = driver.find_element(By.XPATH, "//div[@class='span4'][p[strong[text()='NAICS']]]").text.split(": ")[1]

        data['Site Address'] = site_address
        data['Mailing Address'] = mailing_address
        data['Union Status'] = union_status
        data['SIC'] = sic
        data['NAICS'] = naics

        # Inspection Type, Scope, Ownership 등 정보 추출
        inspection_type = driver.find_element(By.XPATH, "//p[strong[text()='Inspection Type']]").text.split(": ")[1]
        scope = driver.find_element(By.XPATH, "//p[strong[text()='Scope']]").text.split(": ")[1]
        ownership = driver.find_element(By.XPATH, "//p[strong[text()='Ownership']]").text.split(": ")[1]

        data['Inspection Type'] = inspection_type
        data['Scope'] = scope
        data['Ownership'] = ownership

        # Violation Summary 표 추출
        violation_summary = driver.find_element(By.XPATH, "//table[caption[text()='Violation Summary']]")
        rows = violation_summary.find_elements(By.TAG_NAME, "tr")

        for row in rows[1:]:  # 첫 번째 행은 헤더이므로 건너뜁니다.
            cells = row.find_elements(By.TAG_NAME, "td")
            if "Initial Violations" in row.text:
                data['Initial Violations Serious'] = cells[0].text
                data['Initial Violations Willful'] = cells[1].text
                data['Initial Violations Repeat'] = cells[2].text
                data['Initial Violations Other'] = cells[3].text
                data['Initial Violations Unclass'] = cells[4].text
                data['Initial Violations Total'] = cells[5].text
            elif "Current Violations" in row.text:
                data['Current Violations Serious'] = cells[0].text
                data['Current Violations Willful'] = cells[1].text
                data['Current Violations Repeat'] = cells[2].text
                data['Current Violations Other'] = cells[3].text
                data['Current Violations Unclass'] = cells[4].text
                data['Current Violations Total'] = cells[5].text
            elif "Initial Penalty" in row.text:
                data['Initial Penalty'] = cells[5].text
            elif "Current Penalty" in row.text:
                data['Current Penalty'] = cells[5].text

        # 조사 결과 반환
        driver.quit()
        return data

    except Exception as e:
        print(f"Error occurred for Inspection Nr: {inspection_nr}, {str(e)}")
        driver.quit()
        return None

# 텍스트 파일에서 Summary Nr 목록을 읽어옵니다.
def read_summary_nrs_from_file(file_path):
    with open(file_path, 'r') as file:
        summary_nrs = file.read().splitlines()
    return summary_nrs

# 메인 함수
def main(input_file_path):
    summary_nrs = read_summary_nrs_from_file(input_file_path)
    batch_size = 3

    for i in tqdm(range(0, len(summary_nrs), batch_size)):
        batch_summary_nrs = summary_nrs[i:i + batch_size]
        results = []

        for summary_nr in batch_summary_nrs:
            inspection_nr = fetch_inspection_nr(summary_nr)
            if inspection_nr:
                details = fetch_inspection_details(inspection_nr)
                if details:
                    results.append(details)

            # 각 요청 사이에 지연 시간을 추가합니다.
            time.sleep(2)

        # 결과를 DataFrame으로 변환하여 Excel로 저장
        df = pd.DataFrame(results)
        output_file_path = f"inspection-detail/Inspection_Detail({i}~{i + len(batch_summary_nrs)}).xlsx"
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        df.to_excel(output_file_path, index=False)

# 파일 경로를 지정하고 함수를 호출합니다.
if __name__ == "__main__":
    input_file_path = "Summary_Nrs.txt"  # 입력 텍스트 파일의 경로를 입력하세요.
    main(input_file_path)
