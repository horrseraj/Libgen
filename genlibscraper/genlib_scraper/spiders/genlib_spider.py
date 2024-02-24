from typing import Any, Optional
import scrapy

from genlib_scraper.items import BookItem
from models import SearchKey, SearchResult, Author, Book, BookAuthor


class GenlibSpider(scrapy.Spider):
    name = 'genlib'
    # allowed_domains = ['genlib.is']

    def __init__(self, name: str | None = None, **kwargs: Any):
        super().__init__(name, **kwargs)
        self.base_url = 'https://libgen.rs/'
        self.result_per_page = 25
        self.pages_to_scrape = 2

    def start_requests(self):
        search_key = getattr(self, 'search_key', None)
        if search_key:
            # Inser into SearchKey
            new_search = SearchKey.create(search_key=search_key)
            search_id = new_search.id
            
            url = f'{self.base_url}search.php?req={search_key}'
            yield scrapy.Request(url, callback=self.find_pages, cb_kwargs={'search_id': search_id})

    def find_pages(self, response, search_id):
        # Finding number of result pages
        results = response.css('table tr td font::text').get()
        num_results, *other = results.split(" ")
        # finding number of result pages
        if num_results:
            num_results = int(num_results)
            pages = num_results // self.result_per_page + \
                (num_results % self.result_per_page > 0)
            self.pages_to_scrape = pages

        # search_id = response.meta['search_id']
        for i in range(self.pages_to_scrape):
            url = f'{response.url}&page={i+1}'
            #    &open=0&res=25&view=simple&phrase=1&column=def'  # &page={i}'
            yield scrapy.Request(url, callback=self.parse, cb_kwargs={'search_id': search_id})

    def parse(self, response, search_id):
        # Extracting search results
        # search_id = response.meta['search_id']
        # Skip the first <tr> element (header)
        trs = response.css('table.c tr')[1:]
        for tr in trs:
            # Extracting data from each <td> element within the <tr> element
            book_id = tr.css('td:nth-of-type(1)::text').get()
            elements = tr.css('td:nth-of-type(2)')
            author_names = elements.css('a::text').getall()
            authors = ', '.join(author_names)
            title = tr.css('td:nth-of-type(3) a::text').get()
            # link = tr.css('td:nth-child(3) > a:not(:has(font))::attr(href)').get()
            link = tr.xpath('td[3]/a[starts-with(@href, "book")]/@href').extract_first()
            publisher = tr.css('td:nth-of-type(4)::text').get()
            year = tr.css('td:nth-of-type(5)::text').get()
            pages = tr.css('td:nth-of-type(6)::text').get()
            language = tr.css('td:nth-of-type(7)::text').get()
            size = tr.css('td:nth-of-type(8)::text').get()
            extension = tr.css('td:nth-of-type(9)::text').get()

            try:
                year = int(year)
            except (TypeError, ValueError):
                year = 0
            try:
                pages = int(pages)
            except (TypeError, ValueError):
                pages = 0
            # Create an instance of SearchResult and save it to the database
            result = SearchResult.create(
                search_id=search_id,
                book_id=book_id,
                title=title,
                authors=authors,
                publisher=publisher,
                year=year,
                pages=pages,
                language=language,
                size=size,
                extension=extension
            )
            # Check to see if this book_id exists
            try:
                Book.get(Book.id == book_id)
            except Book.DoesNotExist:
                link = self.base_url + link
                yield scrapy.Request(link, callback=self.parse_book, cb_kwargs={'authors': author_names})

    def parse_book(self, response, authors):
        # self.logger.info('Entering parse_book method')
        # self.logger.info('Response URL: %s', response.url)
        # self.logger.info('Response status: %s', response.status)

        html = response.text
        # Select the <tr> elements
        tr_elements = response.css('table tr')[1:23]
        for tr_index, tr in enumerate(tr_elements, start=2):
            # Select the <td> elements within the <tr>
            td_elements = tr.css('td')
            for td_index, td in enumerate(td_elements, start=1):
                if tr_index == 2 and td_index == 1:
                    download_url = td.css('a::attr(href)').get()
                    image_url = td.css('img::attr(src)').get()
                if tr_index == 2 and td_index == 10:
                    title = td.css('a::text').get()
                if tr_index == 12 and td_index == 2:
                    series = td.css('::text').get()
                if tr_index == 12 and td_index == 4:
                    periodical = td.css('::text').get()
                if tr_index == 13 and td_index == 2:
                    publisher = td.css('::text').get()
                if tr_index == 13 and td_index == 4:
                    city = td.css('::text').get()
                if tr_index == 14 and td_index == 2:
                    year = td.css('::text').get()
                if tr_index == 14 and td_index == 4:
                    edition = td.css('::text').get()
                if tr_index == 15 and td_index == 2:
                    language = td.css('::text').get()
                if tr_index == 15 and td_index == 4:
                    pages = td.css('::text').get()
                    try:
                        pages_biblio, pages_tech = pages.split('\\')[:2]
                    except:
                        pages_biblio = None
                        pages_tech = None
                if tr_index == 16 and td_index == 2:
                    isbn = td.css('::text').get()
                    if isbn:
                        isbn10, isbn13 = [part.strip()
                                          for part in isbn.split(',')[:2]]
                        if len(isbn10) > 10:
                            isbn10, isbn13 = isbn13, isbn10
                if tr_index == 16 and td_index == 4:
                    id = td.css('::text').get()
                if tr_index == 17 and td_index == 2:
                    time_added = td.css('::text').get()
                if tr_index == 17 and td_index == 4:
                    time_modified = td.css('::text').get()
                if tr_index == 18 and td_index == 2:
                    library = td.css('::text').get()
                if tr_index == 18 and td_index == 4:
                    library_issue = td.css('::text').get()
                if tr_index == 19 and td_index == 2:
                    size = td.css('::text').get()
                if tr_index == 19 and td_index == 4:
                    extension = td.css('::text').get()
                if tr_index == 20 and td_index == 2:
                    worse_versions = td.css('::text').get()
                if tr_index == 21 and td_index == 2:
                    desr_old_vers = td.css('::text').get()
                if tr_index == 22 and td_index == 2:
                    commentary = td.css('::text').get()
                if tr_index == 23 and td_index == 2:
                    topic = td.css('::text').get()
                if tr_index == 23 and td_index == 4:
                    td_text = td.css('::text').getall()
                    cleaned = [text.strip() for text in td_text if text.strip(
                    ) and text.strip() not in [';', '>>']]
                    tags = ', ' .join(cleaned)

        # Create an instance of Book and save it to the database
        new_book = Book.create(
            id=id,
            title=title,
            series=series,
            publisher=publisher,
            year=year,
            language=language,
            isbn10=isbn10,
            isbn13=isbn13,
            time_added=time_added,
            time_modified=time_modified,
            library=library,
            library_issue=library_issue,
            size=size,
            extension=extension,
            worse_versions=worse_versions,
            Desr_old_vers=desr_old_vers,
            commentary=commentary,
            topic=topic,
            tags=tags,
            periodical=periodical,
            city=city,
            edition=edition,
            pages_biblio=pages_biblio,
            pages_tech=pages_tech,
            html=html
        )
        # Insert Authors if they already dont exist
        # author_names = response.meta['authors']
        for auth in authors:
            try:
                author = Author.get(Author.name == auth)
            except Author.DoesNotExist:
                author = Author.create(name=auth)
            finally:
                # Insert BookAuthor
                BookAuthor.create(book_id=new_book.id,
                                  author_id=author.id)
                
        item = BookItem()
        item['id'] = id
        item["title"] = title
        item['series'] = series
        item['publisher'] = publisher
        item['year'] = year
        item['language'] = language
        item['isbn10'] = isbn10
        item['isbn13'] = isbn13
        item['time_added'] = time_added
        item['time_modified'] = time_modified
        item['library'] = library
        item['library_issue'] = library_issue
        item['size'] = size
        item['extension'] = extension
        item['worse_versions'] = worse_versions
        item['Desr_old_vers'] = desr_old_vers
        item['commentary'] = commentary
        item['topic'] = topic
        item['tags'] = tags
        item['periodical'] = periodical
        item['city'] = city
        item['edition'] = edition
        item['pages_biblio'] = pages_biblio
        item['pages_tech'] = pages_tech
        item['file_urls'] = download_url
        
        yield item
        ext = extension
        # yield scrapy.Request(download_url, callback=self.parse_file, meta={'file_name': id+'_file.'+extension})
        # yield {
            
        #     'file_urls': [download_url]
        # }
        
        ext = image_url.split('.')[-1]
        # yield scrapy.Request(self.base_url + image_url, callback=self.parse_file, meta={'file_name': id+'_pic.'+ext})
        # yield {
        #     'title': title,
        #     'file_urls': [self.base_url + image_url]
        # }
        

    def parse_file(self, response):
        # save the file
        file_name= response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.body)


