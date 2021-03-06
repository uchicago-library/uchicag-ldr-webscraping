import re
import requests
import argparse
from bs4 import BeautifulSoup
import urllib.parse as urlparse
from urllib.parse import urljoin
from os import listdir,stat
from os.path import basename,join,exists,isdir,isfile
from time import sleep,strftime,localtime,mktime
from hashlib import sha256
from logging import DEBUG, FileHandler, Formatter, getLogger, INFO, StreamHandler
from datetime import datetime

from uchicagoldr.bash_cmd import BashCommand

from ldrwebscraping.alerts import Alert
from ldrwebscraping.parseHTML import getLinksByExtension
from ldrwebscraping.download import getPage,downloadFile
from ldrwebscraping.link import isAbsolute,convertToAbs
from ldrwebscraping.administration import readFilesSeen
from ldrwebscraping.handy import hash,countFiles,dirSize


def main():
    parser=argparse.ArgumentParser(description='A program for watching pages containing PDF links and logging when new content is added in order to prepare it for accessioning into the LDR')
    parser.add_argument('url',type=str)
    parser.add_argument('-o','--out-path',type=str,required=True,help='The absolute path to the containing directory.')
    parser.add_argument('-t','--max-time',type=int,default=None,help='The maximum amount of time in seconds that should be able to occur between runs before the Accessioning Specialist is notified to stage the directory contents.')
    parser.add_argument('-n','--max-files',type=int,default=None,help='The maximum number of files in the directory that should be able to accumulate between runs before the Accessioning Specialist is notified to stage the directory contents.')
    parser.add_argument('-s','--max-size',type=int,default=None,help='The maximum filesize in bytes the directory that should be able to accumulate between runs before the Accessioning Specialist is notified to stage the directory contents.')
    args=parser.parse_args()

    log_format=Formatter("[%(levelname)s] %(asctime)s  = %(message)s",datefmt="%Y-%m-%dT%H:%M:%S")
    global logger
    logger=getLogger("lib.uchicago.repository.logger")
    logger.setLevel('DEBUG')
    ch=StreamHandler()
    ch.setFormatter(log_format)
    ch.setLevel('INFO')
    logger.addHandler(ch)

    #Check to be sure the outpath exists, we're writing our log there after all. If it doesn't print to the terminal and exit.
    if not exists(args.out_path) or not isdir(args.out_path):
        logger.critical(args.out_path+" doesn't appear to exist, or isn't a directory!")
        logger.critical('Exiting (1)')
        exit(1)

    fh=FileHandler(args.out_path+'/log.txt')
    fh.setFormatter(log_format)
    fh.setLevel('DEBUG')
    logger.addHandler(fh)

    #Write the date we're doing all this to the log, so we can check it later.
    logger.info("Run begins: "+strftime('%Y-%m-%dT%H:%M:%S'))
    #Download the hub page which contains the links. If we can't get that we can't go anywhere, so exit.
    page=getPage(args.url)
    if page[0] != True:
        logger.critical("Non-200 HTTP resonpse from: "+args.url)
        logger.critical('HTTP Response was: '+str(page[1].status_code))
        logger.critical('Exiting (1)')
        exit(1)
    else:
        logger.info('Connection established with '+args.url)

    #Pull out the links and resolve them to what should *hopefully* be their absolute web-path
    links=getLinksByExtension(page,'pdf')
    links=convertToAbs(args.url,links)

    #Make a tmp directory to download everything this go around
    logger.debug('Creating tmp subdirectory at: '+join(args.out_path,'tmp'))
    mkdirArgs=['mkdir',join(args.out_path,'tmp')]
    mkdirCommand=BashCommand(mkdirArgs)
    assert(mkdirCommand.run_command()[0])
    logger.debug(mkdirCommand.get_data()[1])

    #Download and hash everything we can into the tmp directory. Keep the hashes and filepaths handy in RAM.
    hashPaths=[]
    for link in links:
        logger.info('Downloading '+link+' to '+join(args.out_path,'tmp')+' and hashing.')
        dl=downloadFile(link,join(args.out_path,'tmp'))
        if dl[0] == True:
            filePath=dl[1]
            fileHash=hash(dl[1])
        else:
            filePath=None
            fileHash=None
        hashPaths.append((filePath,fileHash))

    #Read our log of what we've already got (or had) in the directory. Populate another list in memory.
    filesSeen=[]
    if exists(args.out_path+"/filesSeen.txt"):
        logger.info('Reading '+args.out_path+'/filesSeen.txt')
        filesSeen=readFilesSeen(args.out_path+"/filesSeen.txt")

    #For all the new stuff...
    for entry in hashPaths:
        #If we haven't seen it before...
        if entry[1] not in filesSeen:
            logger.info('New File: '+entry[1])
            #Move the file into the primary directory, not clobbering, add them to filesSeen, because we've seen them now.
            if not exists(args.out_path+'/'+basename(entry[0])):
                mvArgs=['mv',entry[0],args.out_path]
            else:
                logger.info('File with a new hash conflicts with an existing filename. Appending the current date string.')
                mvArgs=['mv',entry[0],args.out_path+'/'+basename(entry[0])+"."+strftime('%Y%m%d%H%M%S')+'.pdf']
                pass
            mvCommand=BashCommand(mvArgs)
            assert(mvCommand.run_command()[0])
            logger.debug(mvCommand.get_data()[1])
                
            with open(args.out_path+"/filesSeen.txt",'a') as f:
                f.write(entry[0]+'\t'+entry[1]+'\n')
        #If we haven't seen it before...
        elif entry[1] in filesSeen:
            #Delete the file, its of no use to us because a copy already exists (or did exist) in the parent directory.
            logger.info("Previously seen file: "+entry[1]+". Removing.")
            rmArgs=['rm',entry[0]]
            rmCommand=BashCommand(rmArgs)
            assert(rmCommand.run_command()[0])
            logger.debug(rmCommand.get_data()[1])
        else:
            #Sometimes you just really want to be sure you didn't miss anything
            logger.critical('This shouldn\'t ever run. Universe broken.')
            logger.critical('Exiting (1)')
            exit(1)

    #We should have either moved everything in the tmp directory into the parent directory or deleted it now, so remove the tmp directory.
    rmDirArgs=['rmdir',join(args.out_path,'tmp')]
    rmDirCommand=BashCommand(rmDirArgs)
    assert(rmDirCommand.run_command()[1])
    logger.debug(rmDirCommand.get_data()[1])

    #Lets do some checks to see if we have enough stuff to stage and accession.
    if args.max_time != None:
        lineList=[]
        match=re.compile('^\[INFO\] [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}  \\= Run complete: [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}')
        if exists(args.out_path+"/log.txt"):
            for line in open(args.out_path+"/log.txt","r"):
                lineList.append(line)
            lineList=reversed(lineList)
            for line in lineList:
                    if re.search(match,line):
                        lastRunLine=line
                        break
            lastRunTimeString=lastRunLine.split()[-1]
            lastRunTime=datetime.strptime(lastRunTimeString,'%Y-%m-%dT%H:%M:%S')
            now = datetime.strptime(strftime('%Y-%m-%dT%H:%M:%S'),'%Y-%m-%dT%H:%M:%S') 
            delta=now-lastRunTime
            if delta.seconds > args.max_time:
                alert("This should be staged and accessioned!")
        else:
            logger.warn("You specified a maximum time constraint but there is no existing log. If this isn't the first run in this containing directory this could mean trouble.")
    
    if args.max_files != None:
        numOfFiles=countFiles(args.out_path)-2
        logger.info('Number of files in directory: '+str(numOfFiles))
        if numOfFiles>args.max_files:
            logger.info('This accession contains more files than the specified maximum! It should be staged!')
            alert('This should be staged and accessioned!')
        

    if args.max_size != None:
        size=dirSize(args.out_path)
        logger.info('Directory size: '+str(size)+' bytes.')
        if size > args.max_size:
            logger.info('This accession is larger than the specified max size! It should be staged!')
            alert('This should be staged and accessioned!')

    #The run is complete (and seems to have completed succesfully, write as much to the log.
    logger.info("Run complete: "+strftime('%Y-%m-%dT%H:%M:%S'))

if __name__ == '__main__':
    main()
