from bs4 import BeautifulSoup
with open('/home/jiraiya/codebase/python-learning/Web_scraping/01-Scraping_Basics/home.html', 'r') as html_file:
    content = html_file.read()
    soup = BeautifulSoup(content, 'lxml')
    print(soup.prettify())