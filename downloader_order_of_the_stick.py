from pathlib import Path

from lxml import html as lxml_html

from downloader import Url, Html, ProcessPageResult, download_all_pages


INITIAL_PAGE_URL = 'https://www.giantitp.com/comics/oots0001.html'
OUTPUT_DIR = Path(__file__).resolve().parent / 'OrderOfTheStick'


def process_page(page: Url, html: Html) -> ProcessPageResult:
    tree = lxml_html.fromstring(html)
    tree.make_links_absolute(page)

    next_page_matches = tree.xpath('/html/body/table/tr[2]/td/table/tr/td[2]/table/tr/td/table/tr[1]/td/table/tr/td/a[6]/@href')
    assert len(next_page_matches) == 1
    next_page = next_page_matches[0]
    # The next page URL being the same as the current page URL means that there are no more pages.
    if next_page == page:
        next_page = None

    image_url_matches = tree.xpath('/html/body/table/tr[2]/td/table/tr/td[2]/table/tr/td/table/tr[2]/td/img/@src')
    assert len(image_url_matches) == 1
    image_url = image_url_matches[0]

    return ProcessPageResult(image_url, next_page)


def main() -> None:
    download_all_pages(INITIAL_PAGE_URL, process_page, OUTPUT_DIR)


if __name__ == "__main__":
    main()
