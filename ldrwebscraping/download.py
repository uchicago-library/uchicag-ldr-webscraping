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
    from os.path import basename,exists
    from ldrwebscraping.handy import genRandID
    filename=basename(link)
    page=getPage(link)
    noClobber=False
    if page[0] != True:
        return (False,None,noClobber)
    else:
        while exists(outPath+"/"+filename+suffix):
            suffix=genRandID()
            noClobber=suffix
        with open(outPath+"/"+filename+suffix,'wb') as f:
            for chunk in page[1].iter_content(1024):
                f.write(chunk)
                return (True,outPath+"/"+filename+suffix,noClobber)

def tmpDownloadAndHash(links,out_path):
    from uchicagoldr.bash_cmd  import BashCommand
    from ldrwebscraping.handy import hash
    from os.path import join
    hashPaths=[]
    for link in links:
        dl=downloadFile(link,join(out_path,'tmp'))
        if dl[0] == True:
            filePath=dl[1]
            fileHash=hash(dl[1])
        
            if dl[2] != False:
                if fileHash in [x[1] for x in hashPaths]:
                    rmArgs=['rm',filePath]
                    rmCommand=BashCommand(rmArgs)
                    assert(rmCommand.run_command()[0])
                    logger.debug(rmCommand.get_data()[1])
                    continue
        else:
            filePath=None
            fileHash=None
        hashPaths.append((filePath,fileHash))
    return hashPaths
