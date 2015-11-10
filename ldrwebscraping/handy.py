def hash(filepath,blocksize=65536):
    from hashlib import sha256
    hasher=sha256()
    fileContents=open(filepath,'rb')
    buf=fileContents.read(blocksize)
    while len(buf)>0:
        hasher.update(buf)
        buf=fileContents.read(blocksize)
    return hasher.hexdigest()
    

def countFiles(path,num=0):
    for content in listdir(path):
        if isfile(content):
            num+=1
    for content in listdir(path):
        if isdir(content):
            num+=countFiles(join(path,content))
    return num

def dirSize(path,size=0):
    from os import listdir,isfile,isdir,stat
    for content in listdir(path):
        if isfile(content):
            size+=stat(join(path,content)).st_size
    for content in listdir(path):
        if isdir(content):
            size+=dirSize(join(path,content))
    return size
