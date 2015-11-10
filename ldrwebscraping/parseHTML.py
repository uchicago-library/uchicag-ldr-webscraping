def getLinksByExtension(page,extension):
    from re import compile as re_compile,search
    from bs4 import BeautifulSoup
    match=re_compile('\.'+extension+'$')
    links=[]
    pageText=page[1].text
    pageSoup=BeautifulSoup(pageText,'html.parser')
    for link in pageSoup.find_all('a'):
        try:
            href=link['href']
            if search(match,href):
                links.append(href)
        except KeyError:
            pass
    return links
