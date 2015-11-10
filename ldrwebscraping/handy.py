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
    from os import listdir
    from os.path import isdir,isfile,join
    for content in listdir(path):
        if isfile(join(path,content)):
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

def genRandID(size=6,chars=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']):
    from random import choice
    return ''.join(choice(chars) for _ in range(size))
