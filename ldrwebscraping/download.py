def getPage(url,iteration=0):
    import requests
    iteration+=1
    request=requests.get(url,stream=True)
    if request.status_code == 200:
        return (True,request)
    else:
        if iteration < 6:
            sleep(10)
            getPage(url,iteration=iteration)
        return (False,request)

def downloadFile(link,outPath,suffix=""):
    from os.path import basename
    filename=basename(link)
    page=getPage(link)
    if page[0] != True:
        return (False,None)
    else:
        with open(outPath+"/"+filename+suffix,'wb') as f:
            for chunk in page[1].iter_content(1024):
                f.write(chunk)
                return (True,outPath+"/"+filename+suffix)
        logger.debug('File written.')
