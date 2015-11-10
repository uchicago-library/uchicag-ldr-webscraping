def readFilesSeen(filepath):
    from os.path import exists
    hashes=[]
    if exists(filepath+"/filesSeen.txt"):
        f=open(filepath+"/filesSeen.txt",'r')
        for line in f.readlines():
            line=line.rstrip('\n')
            if len(line) > 0:
                fileHash=line.split("\t")[-1]
                hashes.append(fileHash)
        f.close()
    return hashes

def saneTargetDir(dirpath):
    from os.path import exists,isdir
    if not exists(dirpath) or not isdir(dirpath):
        return False
    return True
