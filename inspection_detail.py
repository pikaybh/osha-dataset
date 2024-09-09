import logging
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from typing import List, Optional, Dict, Any
import argparse
import re
import pickle

# Logger 설정
logger_name = 'inspection_detail'
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)

# File Handler 설정
file_handler = logging.FileHandler(f'logs/{logger_name}.log', encoding='utf-8-sig')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(r'%(asctime)s [%(name)s, line %(lineno)d] %(levelname)s: %(message)s'))
logger.addHandler(file_handler)

# Stream Handler 설정
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(r'%(message)s'))
logger.addHandler(stream_handler)

def sanitize_string(input_string: str) -> str:
    """Remove illegal characters for Excel and control characters."""
    illegal_characters = re.compile(r'[\x00-\x1F\x7F-\x9F]')
    return illegal_characters.sub("", input_string)

class OSHAWebScraper:
    def __init__(self, driver_service: Service, chrome_options: Options, retry_count: int = 3) -> None:
        self.driver_service = driver_service
        self.chrome_options = chrome_options
        self.retry_count = retry_count

    def _start_driver(self) -> webdriver.Chrome:
        return webdriver.Chrome(service=self.driver_service, options=self.chrome_options)

    def _extract_text(self, driver: webdriver.Chrome, name: str, xpath: str, transform: bool = False) -> Dict[str, str]:
        try:
            text = driver.find_element(By.XPATH, xpath).text
            if transform:
                text = text.replace("\n", ", ")
            return {name: sanitize_string(text.split(": ")[1] if ": " in text else text.split(":")[1] if ":" in text else text)}
        except Exception as e:
            logger.error(e)
            logger.warning(f"Failed to extract {name} using xpath: {xpath}")
            return {name: ''}

    def _retry_get(self, driver: webdriver.Chrome, url: str):
        for attempt in range(self.retry_count):
            try:
                driver.get(url)
                return True
            except Exception as e:
                logger.warning(f"Retrying ({attempt + 1}/{self.retry_count}) to load URL: {url}")
                time.sleep(2)
        return False

    def fetch_inspection_details(self, inspection_nr: str) -> Dict[str, Any]:
        driver = self._start_driver()
        url = f"https://www.osha.gov/ords/imis/establishment.inspection_detail?id={inspection_nr}"

        if not self._retry_get(driver, url):
            logger.error(f"Failed to load page for Inspection Nr: {inspection_nr} after retries.")
            driver.quit()
            return None

        data = {}
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.row-fluid"))
            )

            # 기본 정보 추출
            data["Inspection Office"] = sanitize_string(driver.find_element(By.XPATH, "//p/strong[contains(text(), 'Inspection Information - Office')]").text.split(": ")[-1])
            data.update(self._extract_text(driver, "Inspection Nr", "//div[@class='span4'][strong[text()='Inspection Nr']]"))
            data.update(self._extract_text(driver, "Report ID", "//div[@class='span4'][strong[text()='Report ID']]"))
            data.update(self._extract_text(driver, "Date Opened", "//div[@class='span4'][strong[text()='Date Opened']]"))
            data.update(self._extract_text(driver, "Case Status", "//div[@class='well well-small']"))
            data.update(self._extract_text(driver, "Site Address", "//p[strong[text()='Site Address']]", transform=True))
            data.update(self._extract_text(driver, "Mailing Address", "//p[strong[text()='Mailing Address']]", transform=True))
            data.update(self._extract_text(driver, "Union Status", "//div[@class='span4'][p[strong[text()='Union Status']]]"))
            data.update(self._extract_text(driver, "SIC", "//p[strong[text()='SIC']]"))
            data.update(self._extract_text(driver, "NAICS", "//p[strong[text()='NAICS']]"))
            data.update(self._extract_text(driver, "Inspection Type", "//p[strong[text()='Inspection Type']]"))
            data.update(self._extract_text(driver, "Scope", "//p[strong[text()='Scope']]"))
            data.update(self._extract_text(driver, "Advanced Notice", "//p[strong[text()='Advanced Notice']]"))
            data.update(self._extract_text(driver, "Ownership", "//p[strong[text()='Ownership']]"))
            data.update(self._extract_text(driver, "Safety/Health", "//p[strong[text()='Safety/Health']]"))
            data.update(self._extract_text(driver, "Close Conference", "//p[strong[text()='Close Conference']]"))
            data.update(self._extract_text(driver, "Emphasis", "//p[strong[text()='Emphasis']]"))
            data.update(self._extract_text(driver, "Case Closed", "//p[strong[text()='Case Closed']]"))

            # Related Activity 테이블 추출
            try:
                related_activity = driver.find_element(By.XPATH, "//table[caption[text()='Related Activity']]")
                related_activity_rows = related_activity.find_elements(By.TAG_NAME, "tr")[1:]  # 첫 번째 행은 헤더이므로 건너뜀
                for idx, row in enumerate(related_activity_rows, start=1):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    data.update({
                        f"Related Activity Type {idx}": sanitize_string(cells[0].text),
                        f"Related Activity Nr {idx}": sanitize_string(cells[1].text),
                        f"Related Activity Safety {idx}": sanitize_string(cells[2].text),
                        f"Related Activity Health {idx}": sanitize_string(cells[3].text),
                    })
            except Exception:
                logger.warning(f"Related Activity table not found for Inspection Nr: {inspection_nr}")

            # Violation Summary 추출
            try:
                violation_summary = driver.find_element(By.XPATH, "//table[caption[text()='Violation Summary']]")
                rows = violation_summary.find_elements(By.TAG_NAME, "tr")
                for row in rows[1:]:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    label = row.find_element(By.TAG_NAME, "th").text
                    data.update({
                        f'{label} Serious': sanitize_string(cells[0].text),
                        f'{label} Willful': sanitize_string(cells[1].text),
                        f'{label} Repeat': sanitize_string(cells[2].text),
                        f'{label} Other': sanitize_string(cells[3].text),
                        f'{label} Unclass': sanitize_string(cells[4].text),
                        f'{label} Total': sanitize_string(cells[5].text)
                    })
            except Exception:
                logger.warning(f"Violation Summary table not found for Inspection Nr: {inspection_nr}")

            # Violation Items 추출 (누락된 부분 추가)
            try:
                violation_items = driver.find_element(By.XPATH, "//table[caption[text()='Violation Items']]")
                rows = violation_items.find_elements(By.TAG_NAME, "tr")
                for idx, row in enumerate(rows[1:], start=1):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    data.update({
                        f"Violation Item {idx} Citation ID": sanitize_string(cells[0].text),
                        f"Violation Item {idx} Citation Type": sanitize_string(cells[1].text),
                        f"Violation Item {idx} Standard Cited": sanitize_string(cells[2].text),
                        f"Violation Item {idx} Issuance Date": sanitize_string(cells[3].text),
                        f"Violation Item {idx} Abatement Due Date": sanitize_string(cells[4].text),
                        f"Violation Item {idx} Current Penalty": sanitize_string(cells[5].text),
                        f"Violation Item {idx} Initial Penalty": sanitize_string(cells[6].text),
                        f"Violation Item {idx} FTA Penalty": sanitize_string(cells[7].text),
                        f"Violation Item {idx} Contest": sanitize_string(cells[8].text),
                        f"Violation Item {idx} Latest Event": sanitize_string(cells[9].text),
                        f"Violation Item {idx} Note": sanitize_string(cells[10].text),
                    })
            except Exception:
                logger.warning(f"Violation Items table not found for Inspection Nr: {inspection_nr}")

            # Investigation Summary 추출
            try:
                investigation_summary = driver.find_element(By.XPATH, "//h4[strong[text()='Investigation Summary']]")
                investigation_rows = investigation_summary.find_elements(By.XPATH, ".//following-sibling::div[contains(@class, 'row-fluid')]/div")
                for idx, div in enumerate(investigation_rows):
                    if ": " in div.text:
                        text = div.text.split(": ")
                        data[text[0]] = sanitize_string(text[1])
                    else:
                        data["Investigation Summary Short"] = sanitize_string(div.text)
                data["Investigation Summary Long"] = sanitize_string(investigation_summary.find_elements(By.XPATH, ".//following-sibling::p")[0].text)
                # Keywords 추출
                try:
                    data.update(self._extract_text(driver, "Keywords", "//p[strong[text()='Keywords:']]"))
                except:
                    data.update(self._extract_text(driver, "Keywords", "//p[strong[text()='Keywords']]"))
            except Exception:
                logger.warning(f"Investigation Summary not found for Inspection Nr: {inspection_nr}")

        except Exception as e:
            logger.error(f"Error occurred for Inspection Nr: {inspection_nr}, {str(e)}")

        driver.quit()
        return data

class InspectionDataProcessor:
    def __init__(self, scraper: OSHAWebScraper, checkpoint_file: str) -> None:
        self.scraper = scraper
        self.checkpoint_file = checkpoint_file

    def _load_checkpoint(self) -> int:
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as file:
                return int(file.read().strip())
        return 0

    def _save_checkpoint(self, index: int) -> None:
        with open(self.checkpoint_file, 'w') as file:
            file.write(str(index))

    def _get_last_processed_index(self, output_dir: str) -> int:
        files = sorted([f for f in os.listdir(output_dir) if f.endswith('.xlsx')])
        if files:
            last_file = files[-1]
            last_index = int(last_file.split('(')[-1].split('~')[0])
            return last_index + 1
        return 0

    def _save_pickle(self, data: List[Dict[str, Any]], i: int, output_dir: str) -> None:
        pickle_file = os.path.join(output_dir, f"pkls/Inspection_Detail({i}).pkl")
        os.makedirs(os.path.dirname(pickle_file), exist_ok=True)
        with open(pickle_file, 'wb') as file:
            pickle.dump(data, file)
        logger.info(f"Saved batch {i} as pickle to {pickle_file}")

    def _load_latest_pickle(self, output_dir: str) -> Optional[List[Dict[str, Any]]]:
        pickle_files = sorted([f for f in os.listdir(os.path.join(output_dir, 'pkls')) if f.endswith('.pkl')])
        if pickle_files:
            latest_pickle_file = pickle_files[-1]
            pickle_path = os.path.join(output_dir, 'pkls', latest_pickle_file)
            with open(pickle_path, 'rb') as file:
                data = pickle.load(file)
            logger.info(f"Loaded data from {pickle_path}")
            return data
        return None

    def process_inspections(self, inspection_nrs: List[str], output_dir: str, batch_size: int, sleep_time: int) -> None:
        last_processed = max(self._load_checkpoint(), self._get_last_processed_index(output_dir))

        for i in tqdm(range(last_processed, len(inspection_nrs), batch_size)):
            batch_inspection_nrs = inspection_nrs[i:i + batch_size]
            results = []

            for inspection_nr in tqdm(batch_inspection_nrs, desc=f"{i}th batch"):
                details = self.scraper.fetch_inspection_details(inspection_nr)
                logger.debug(f"{details = }")
                if details:
                    results.append(details)

                time.sleep(sleep_time)

            if results:
                df = pd.DataFrame(results)
                output_file_path = os.path.join(output_dir, f"Inspection_Detail({i}~{i + len(batch_inspection_nrs)}).xlsx")
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                try:
                    df.to_excel(output_file_path, index=False)
                    logger.info(f"Saved batch {i} to {output_file_path}")
                except Exception as e:
                    logger.error(f"Failed to save batch {i} to Excel due to error: {e}")
                self._save_pickle(results, i, output_dir)

            self._save_checkpoint(i)

        # Check for any remaining unsaved pickle files
        latest_pickle_data = self._load_latest_pickle(output_dir)
        if latest_pickle_data:
            df = pd.DataFrame(latest_pickle_data)
            output_file_path = os.path.join(output_dir, f"Inspection_Detail({last_processed}).xlsx")
            try:
                df.to_excel(output_file_path, index=False)
                logger.info(f"Updated Excel file from latest pickle at {output_file_path}")
            except Exception as e:
                logger.error(f"Failed to update Excel from latest pickle due to error: {e}")

def main(input_file_path: str, output_dir: str, checkpoint: str, batch_size: int, sleep_time: int) -> None:
    # 출력 디렉터리가 없으면 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument(f"--user-data-dir={os.path.join(os.getcwd(), 'chrome_user_data')}")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-extensions")

    driver_service = Service(ChromeDriverManager().install())
    scraper = OSHAWebScraper(driver_service, chrome_options)

    processor = InspectionDataProcessor(scraper, checkpoint)
    # 입력 파일 확장자에 따라 처리 방식 결정
    if input_file_path.endswith('.txt'):
        # 텍스트 파일에서 각 라인을 읽어서 리스트로 변환
        with open(input_file_path, 'r') as file:
            inspection_nrs = file.read().splitlines()
    elif input_file_path.endswith('.xlsx'):
        # 엑셀 파일에서 'Inspection Nr' 컬럼을 읽어서 리스트로 변환
        inspection_nrs = pd.read_excel(input_file_path)['Inspection Nr'].tolist()
    else:
        logger.error("Unsupported file format. Please provide a .txt or .xlsx file.")
        return

    processor.process_inspections(inspection_nrs, output_dir, batch_size, sleep_time)

# Main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape OSHA inspection details.")
    parser.add_argument('--input-file_path', '-I', default="Inspection Nrs.txt", type=str, help='Path to the input file containing Inspection Nrs')
    parser.add_argument('--output-directory', '-O', default="inspection-detail", type=str, help='Path to the output folder')
    parser.add_argument('--checkpoint', '-P', default="inspection-detail/checkpoint", type=str, help='Checkpoint')
    parser.add_argument("--batch-size", '-B', type=int, default=1_000, help="Number of inspections to process in one batch.")
    parser.add_argument("--sleep-time", '-S', type=int, default=2, help="Time to sleep between processing each inspection.")
    args = parser.parse_args()

    main(args.input_file_path, args.output_directory, args.checkpoint, args.batch_size, args.sleep_time)
