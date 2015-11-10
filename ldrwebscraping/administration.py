def readFilesSeen(filepath):
    hashes=[]
    f=open(filepath,'r')
    for line in f.readlines():
        line=line.rstrip('\n')
        if len(line) > 0:
            fileHash=line.split("\t")[-1]
            hashes.append(fileHash)
    f.close()
    return hashes
