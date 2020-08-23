import dataclasses
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Callable, NewType
from urllib.parse import urlparse

import requests


DOWNLOAD_STATE_FILENAME = 'DownloadState.json'


Url = NewType('Url', str)
Html = NewType('Html', bytes)


def download(url: Url) -> requests.Response:
    response = requests.get(url)
    response.raise_for_status()
    return response


def download_binary_to_disk(local_path: Path, url: Url) -> None:
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with local_path.open('wb') as image_file:
            for chunk in response.iter_content(chunk_size=None):
                image_file.write(chunk)


@dataclasses.dataclass
class DownloadState:
    last_page_index: int
    last_page_url: Url


@dataclasses.dataclass
class ProcessPageResult:
    image: Url
    # None means that there are no more pages.
    next_page: Url


def download_all_pages(
    initial_page_url: Url,
    process_page_func: Callable[[Html], ProcessPageResult],
    output_dir: Path
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read existing download state.
    download_state_path = Path(output_dir / DOWNLOAD_STATE_FILENAME)
    if download_state_path.exists():
        download_state_dict = json.loads(download_state_path.read_text(encoding='utf-8'))
        download_state = DownloadState(**download_state_dict)
        # Restore the next page URL.
        try:
            page_response = download(download_state.last_page_url)
        except requests.exceptions.RequestException as ex:
            print(f'Failed to download {download_state.last_page_url}: {ex}')
            return
        process_page_result = process_page_func(download_state.last_page_url, page_response.content)
        page_url = process_page_result.next_page
    else:
        download_state = DownloadState(last_page_index=0, last_page_url=None)
        page_url = initial_page_url

    while True:
        page_index = download_state.last_page_index + 1

        if page_url is None:
            print('No more pages')
            break

        print(f'Downloading {page_url}')
        try:
            page_response = download(page_url)
        except requests.exceptions.RequestException as ex:
            print(f'Failed to download {page_url}: {ex}')
            break
        process_page_result = process_page_func(page_url, page_response.content)

        # Write the image to "{output_dir}/{image-URL-hash.image-extension}".
        image_url = process_page_result.image
        image_url_hash = sha256(image_url.encode('utf-8')).hexdigest()
        image_ext = os.path.splitext(urlparse(image_url).path)[1]
        image_filename = f'{page_index:05}-{image_url_hash}{image_ext}'
        image_path = output_dir / image_filename
        try:
            download_binary_to_disk(image_path, image_url)
        except requests.exceptions.RequestException as ex:
            print(f'Failed to download {image_url}: {ex}')
            break

        download_state.last_page_index = page_index
        download_state.last_page_url = page_url
        download_state_str = json.dumps(dataclasses.asdict(download_state), indent=4)
        download_state_path.write_text(download_state_str, encoding='utf-8')

        page_url = process_page_result.next_page
