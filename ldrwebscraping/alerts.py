#this is a stand in function
def Alert(message):
    print(message)

def determineAlert(args):
    from re import compile as re_compile, search
    from os.path import exists
    from time import sleep,strftime,localtime,mktime
    from datetime import datetime

    from ldrwebscraping.handy import countFiles

    if args.max_time != None:
        lineList=[]
        match=re_compile('^\[INFO\] [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}  \\= Run complete: [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}')
        if exists(args.out_path+"/log.txt"):
            for line in open(args.out_path+"/log.txt","r"):
                lineList.append(line)
            lineList=reversed(lineList)
            for line in lineList:
                    if search(match,line):
                        lastRunLine=line
                        break
            lastRunTimeString=lastRunLine.split()[-1]
            lastRunTime=datetime.strptime(lastRunTimeString,'%Y-%m-%dT%H:%M:%S')
            now = datetime.strptime(strftime('%Y-%m-%dT%H:%M:%S'),'%Y-%m-%dT%H:%M:%S') 
            delta=now-lastRunTime
            if delta.seconds > args.max_time:
                return True
    
    if args.max_files != None:
        numOfFiles=countFiles(args.out_path)-2
        if numOfFiles>args.max_files:
            return True

    if args.max_size != None:
        size=dirSize(args.out_path)
        if size > args.max_size:
            return True
    else:
        return False
