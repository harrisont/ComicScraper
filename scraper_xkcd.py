from pathlib import Path

from lxml import html as lxml_html

from scraper import Url, Html, ProcessPageResult, download_all_pages


INITIAL_PAGE_URL = 'https://xkcd.com/1/'
OUTPUT_DIR = Path(__file__).resolve().parent / 'downloads' / 'xkcd'


def process_page(page: Url, html: Html) -> ProcessPageResult:
    tree = lxml_html.fromstring(html)
    tree.make_links_absolute(page)

    next_page_matches = tree.xpath('/html/body/div[2]/ul[1]/li[4]/a/@href')
    assert len(next_page_matches) == 1
    next_page = next_page_matches[0]
    # The next page URL being the same as the current page URL means that there are no more pages.
    if next_page == page:
        next_page = None

    image_url_matches = tree.xpath('//*[@id="comic"]//img/@src')
    assert len(image_url_matches) == 1
    image_url = image_url_matches[0]

    return ProcessPageResult(image_url, next_page)


def main() -> None:
    download_all_pages(INITIAL_PAGE_URL, process_page, OUTPUT_DIR)


if __name__ == "__main__":
    main()
