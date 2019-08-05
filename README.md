# PySitemap

Simple sitemap generator with Python 3

## Description
This is simple and easy sitemap generator written in python which can help you easily create sitemap of your website for SEO and other purposes.

## Options
Simply you can run with this command and program will create sitemap.xml with links from url option
```
python main.py --url="https://www.finstead.com"
```

If you want the search to include all subdomains like docs.finstead.com
```
python main.py --url="https://www.finstead.com" --domain="finstead.com"
```

If you want custom path for sitemap file you can add `--output` option like below
```
python main.py --url="https://www.finstead.com" --output="/custom/path/sitemap.xml"
```

By default program will print parsing urls in console, but if you want to run silently you can add `--no-verbose` option.
```
python main.py --url="https://www.finstead.com" --no-verbose
```

If you want to restrict some urls from being visited by crawler you can exclude them with regex pattern using `--exclude` option. Below code will exclude `png` or `jpg` files
```
python main.py --url="https://www.finstead.com" --exclude="\.jpg|\.png"
```

You can also use several filters to exclude
```
python main.py --url="https://www.finstead.com" --exclude=".jpg .png"
```

You can run the crawler asynchronously (experimental)
```
python main.py --url="https://www.finstead.com" --asynchronous
```

You can specify timeout for http requests (only in asynchronous mode)
```
python main.py --url="https://www.finstead.com" --timeout=300
```

You can specify how many times should we retry urls that returned with errors (only in asynchronous mode)
```
python main.py --url="https://www.finstead.com" --retry=1
```

You can specify the maximum numbers of simultaneous get requests the crawler can send (only in asynchronous mode)
```
python main.py --url="https://www.finstead.com" --max-requests=100
```

## Usage

```python
from pysitemap.async_crawler import Crawler
# or 
# from pysitemap.crawler import Crawler

crawler = Crawler(url, exclude=exclude, domain=domain, no_verbose=True,
                  timeout=300, retry_times=1, max_requests=100, build_graph=True)

with open('sitemap.xml', 'w') as file:
    file.write(crawler.generate_sitemap())

# You can also generate a graph (in json and gexf formats)
from pysitemap import readwrite
graph = crawler.generate_graph()
# This will generate graph.gexf files in the given directory
readwrite.extract_graph(readwrite.convert_graph(graph), dir_path)
```

## Notice

This code is a fork of https://github.com/Cartman720/PySitemap and https://github.com/swi-infra/PySitemap