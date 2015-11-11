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

def sortTemp(hashPaths,filesSeen,out_path):
    from uchicagoldr.bash_cmd import BashCommand
    from os.path import basename,exists
    from time import strftime

    moved=[]
    removed=[]
    #For all the new stuff...
    for entry in hashPaths:
        #If we haven't seen it before...
        if entry[1] not in filesSeen:
            #Move the file into the primary directory, not clobbering, add them to filesSeen, because we've seen them now.
            if not exists(out_path+'/'+basename(entry[0])):
                mvArgs=['mv',entry[0],out_path]
            else:
                mvArgs=['mv',entry[0],out_path+'/'+basename(entry[0])+"."+strftime('%Y%m%d%H%M%S')]
            mvCommand=BashCommand(mvArgs)
            assert(mvCommand.run_command()[0])
            moved.append(entry)
                
        #If we have seen it before...
        elif entry[1] in filesSeen:
            #Delete the file, its of no use to us because a copy already exists (or did exist) in the parent directory.
            rmArgs=['rm',entry[0]]
            rmCommand=BashCommand(rmArgs)
            assert(rmCommand.run_command()[0])
            removed.append(entry)
    return (moved,removed)

def appendToFilesSeen(filepath,hashPaths):
    with open(filepath+"/filesSeen.txt",'a') as f:
        for entry in hashPaths:
            f.write(entry[0]+'\t'+entry[1]+'\n')
        return True
