from typing import Dict, List, Optional, Union
from tqdm import tqdm
import pandas as pd
import logging
import fire
import os

# Root 
logger_name = 'inspection_detail_merger'
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)
# File Handler
file_handler = logging.FileHandler(f'../logs/{logger_name}.log', encoding='utf-8-sig')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(r'%(asctime)s [%(name)s, line %(lineno)d] %(levelname)s: %(message)s'))
logger.addHandler(file_handler)
# Stream Handler
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(r'%(message)s'))
logger.addHandler(stream_handler)


class FileChunk:
    def __init__(self, files: List[str]) -> None:
        """FileChunk 클래스의 초기화 메서드.

        Args:
            files (List[str]): 파일 이름의 리스트.
        """
        self._files: List[str] = files
        self._data: Dict[str, List[str]] = {}
        self._process_files()

    def _process_files(self) -> None:
        """파일 리스트를 처리하여 확장자별로 분류해 `_data`에 저장합니다."""
        for file in self._files:
            ext = file.split('.')[-1]  # 파일 확장자 추출
            if ext not in self._data:
                self._data[ext] = []
            self._data[ext].append(file)

    @property
    def data(self) -> Dict[str, List[str]]:
        """확장자별로 분류된 파일 리스트를 반환합니다.

        Returns:
            Dict[str, List[str]]: 확장자별로 파일이 분류된 딕셔너리.
        """
        return self._data

    @data.setter
    def data(self, files: List[str]) -> None:
        """새로운 파일 리스트를 설정하고, 확장자별로 다시 분류합니다.

        Args:
            files (List[str]): 새로 설정할 파일 리스트.
        """
        self._files = files
        self._data.clear()
        self._process_files()

    def __call__(self, ext: Optional[Union[str, List[str]]] = None) -> Union[List[str], Dict[str, List[str]]]:
        """특정 확장자 또는 확장자 리스트에 해당하는 파일 리스트를 반환합니다. 
        매개변수가 없으면 전체 파일 리스트를 반환합니다.

        Args:
            ext (Optional[Union[str, List[str]]]): 반환할 파일의 확장자 또는 확장자 리스트. 
            기본값은 None이며, 이 경우 모든 파일을 반환합니다.

        Returns:
            Union[List[str], Dict[str, List[str]]]: 
            - ext가 `str`일 경우: 해당 확장자의 파일 리스트.
            - ext가 `List[str]`일 경우: 확장자별 파일 리스트를 담은 딕셔너리.
            - ext가 `None`일 경우: 모든 파일 리스트.
        """
        if isinstance(ext, str):
            return self._data.get(ext, [])
        elif isinstance(ext, list):
            result = {e: self._data.get(e, []) for e in ext}
            return result
        else:
            all_files = []
            for files in self._data.values():
                all_files.extend(files)
            return all_files


def main(folder: Optional[str] = "./", ext: Optional[Union[str, List[str]]] = "xlsx", output: Optional[str] = "../output") -> None:
    df_list: List[pd.DataFrame] = []
    file_chunks: FileChunk = FileChunk(os.listdir(folder))
    for file in tqdm(file_chunks(ext)):
        df_list.append(pd.read_excel(os.path.join(folder, file)))
    pd.concat(df_list, ignore_index=True).to_excel(os.path.join(output, "Inspection_Details.xlsx"), index=False)

# Main
if __name__ == '__main__':
    fire.Fire(main)
