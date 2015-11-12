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

def downloadFile(link,outPath,suffix="",prefix="",filename=None):
    from os.path import basename,exists
    from ldrwebscraping.handy import genRandID
    if filename == None:
        filename=basename(link)
    page=getPage(link)
    noClobber=False
    if page[0] != True:
        return (False,None,noClobber)
    else:
        while exists(outPath+"/"+prefix+filename+suffix):
            suffix=genRandID()
            noClobber=suffix
        with open(outPath+"/"+prefix+filename+suffix,'wb') as f:
            for chunk in page[1].iter_content(1024):
                f.write(chunk)
                return (True,outPath+"/"+prefix+filename+suffix,noClobber)

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
                    continue
        else:
            filePath=None
            fileHash=None
        hashPaths.append((filePath,fileHash))
    return hashPaths

def tmpDownloadAndHashRSS(feed,out_path,filesSeen=[],dlLinks=False,dlPDFs=False):
    from os.path import join,exists
    from json import dumps

    from uchicagoldr.bash_cmd  import BashCommand
    from ldrwebscraping.handy import hash,genRandID

    hashPaths=[]
    tmpDir=join(out_path,'tmp')
    for entry in feed['entries']:
        outfilename=genRandID()
        while exists(out_path+"/"+outfilename) or exists(tmpDir+"/"+outfilename):
            outfilename=genRandID()
        with open(tmpDir+"/"+outfilename+'.json','w') as f:
            f.write(dumps(entry,indent=4,sort_keys=True))
        filePath=tmpDir+"/"+outfilename+'.json'
        fileHash=hash(filePath)
        hashPaths.append((filePath,fileHash))

        if 'link' in entry and dlLinks:
            seenLink=False
            dl=downloadFile(entry['link'],tmpDir,prefix=outfilename)
            if dl[0] == True:
                linkfilePath=dl[1]
                linkfileHash=hash(dl[1])
                if linkfileHash in filesSeen:
                    seenLink=True
        
                if dl[2] != False:
                    if linkfileHash in [x[1] for x in hashPaths]:
                        seenLink=True
                        rmArgs=['rm',linkfilePath]
                        rmCommand=BashCommand(rmArgs)
                        assert(rmCommand.run_command()[0])
                        continue
            else:
                linkfilePath=None
                linkfileHash=None
            hashPaths.append((linkfilePath,linkfileHash))
            if not seenLink and dlPDFs:
                try:
                    wkhtmltopdfArgs=['wkhtmltopdf',entry['link'],tmpDir+"/"+outfilename+".pdf"]
                    wkhtmltopdfCommand=BashCommand(wkhtmltopdfArgs)
                    wkhtmltopdfCommand.run_command()
                except:
                    pass
                if exists(tmpDir+"/"+outfilename+'.pdf'):
                    pdfFilePath=tmpDir+"/"+outfilename+'.pdf'
                    pdfFileHash=hash(pdfFilePath)
                    hashPaths.append((pdfFilePath,pdfFileHash)) 
    return hashPaths
