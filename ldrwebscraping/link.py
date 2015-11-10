def isAbsolute(url):
    from urllib import parse as urlparse
    return bool(urlparse.urlparse(url).netloc)

def convertToAbs(url,links):
    from urllib.parse import urljoin
    convdLinks=[]
    for link in links:
        if not isAbsolute(link):
            abslink=urljoin(url,link)
            convdLinks.append(abslink)
        else:
            convdLinks.append(link)
    return convdLinks
