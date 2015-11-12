import argparse
import feedparser
from os.path import join,basename,isfile
from json import loads
from logging import DEBUG, FileHandler, Formatter, getLogger, INFO, StreamHandler

from uchicagoldr.bash_cmd import BashCommand

from ldrwebscraping.alerts import Alert,determineAlert
from ldrwebscraping.download import tmpDownloadAndHashRSS
from ldrwebscraping.administration import readFilesSeen,saneTargetDir,sortTemp,appendToFilesSeen
from ldrwebscraping.handy import hash,countFiles,dirSize


def main():
    parser=argparse.ArgumentParser(description='A program for watching pages containing PDF links and logging when new content is added in order to prepare it for accessioning into the LDR')
    parser.add_argument('url',type=str)
    parser.add_argument('-o','--out-path',type=str,required=True,help='The absolute path to the containing directory.')
    parser.add_argument('-t','--max-time',type=int,default=None,help='The maximum amount of time in seconds that should be able to occur between runs before the Accessioning Specialist is notified to stage the directory contents.')
    parser.add_argument('-n','--max-files',type=int,default=None,help='The maximum number of files in the directory that should be able to accumulate between runs before the Accessioning Specialist is notified to stage the directory contents.')
    parser.add_argument('-s','--max-size',type=int,default=None,help='The maximum filesize in bytes the directory that should be able to accumulate between runs before the Accessioning Specialist is notified to stage the directory contents.')
    parser.add_argument('--download-links',default=False,action='store_true',help='Set whether or not to download the links article RSS entries point to.')
    parser.add_argument('--download-pdfs',default=False,action='store_true',help='Assuming --download links is set to True. Set whether or not to create PDFs of the pages which links point to.')
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
    if not saneTargetDir(args.out_path):
        logger.critical(args.out_path+" doesn't appear to exist, or isn't a directory!")
        logger.critical('Exiting (1)')
        exit(1)

    fh=FileHandler(args.out_path+'/log.txt')
    fh.setFormatter(log_format)
    fh.setLevel('DEBUG')
    logger.addHandler(fh)

    #Write the date we're doing all this to the log, so we can check it later.
    logger.info("Run begins.")
    #Download the hub page which contains the links. If we can't get that we can't go anywhere, so exit.
    try:
        feed=feedparser.parse(args.url)
    except Exception as e:
        logger.critical("Attempting the parse the feed caused an exception. Exiting (1).")
        logger.critical(str(e))

    logger.info('Connection established with '+args.url)

    #Make a tmp directory to download everything this go around
    logger.info('Creating tmp subdirectory at: '+join(args.out_path,'tmp'))
    mkdirArgs=['mkdir',join(args.out_path,'tmp')]
    mkdirCommand=BashCommand(mkdirArgs)
    assert(mkdirCommand.run_command()[0])
    logger.debug(mkdirCommand.get_data()[1])

    #Read our log of what we've already got (or had) in the directory. Populate another list in memory.
    logger.info("Reading filesSeen.txt.")
    filesSeen=readFilesSeen(args.out_path)
    logger.debug("Found "+str(len(filesSeen))+" entries in filesSeen.txt")
    for entry in filesSeen:
        logger.debug(entry)

    #Download and hash everything we can into the tmp directory. Keep the hashes and filepaths handy in RAM.
    logger.info('Downloading files into the tmp directory for hashing and comparison.')
    hashPaths=tmpDownloadAndHashRSS(feed,args.out_path,filesSeen=filesSeen,dlLinks=args.download_links,dlPDFs=args.download_pdfs)
    logger.info('Downloaded '+str(len(hashPaths))+' files.')
    for entry in hashPaths:
        logger.debug('Downloaded file: '+entry[0])
        logger.debug('File hash: '+entry[1])


    logger.info('Sorting the contents of the temp directory.')
    moved,removed=sortTemp(hashPaths,filesSeen,args.out_path)
    logger.info(str(len(moved))+" new files found.")
    for entry in moved:
        logger.debug('SAVED: '+" ".join(entry))
    for entry in removed:
        logger.debug('REMOVED: '+" ".join(entry))

    assert(appendToFilesSeen(args.out_path,moved)==True)

    #We should have either moved everything in the tmp directory into the parent directory or deleted it now, so remove the tmp directory.
    logger.info("Removing temp directory.")
    rmDirArgs=['rmdir',join(args.out_path,'tmp')]
    rmDirCommand=BashCommand(rmDirArgs)
    assert(rmDirCommand.run_command()[1])
    logger.debug(rmDirCommand.get_data()[1])

    #Build/append to an index for each file we just moved
    if len(moved)>0:
        logger.info("Building Index for moved files")
        with open(args.out_path+"/index.txt",'a') as f:
            movedArticles=[x for x in moved if '.json' in x[0]]
            for  article in movedArticles:
                newLocation=args.out_path+"/"+basename(article[0])
                if not isfile(newLocation):
                    logger.warn("Can't add "+article[0]+" to the index, it doesn't appear to exist in the directory where it should.")
                    continue
                articleDict=loads("\n".join(line for line in open(newLocation,'r').readlines()))
                title=""
                try:
                    title=articleDict['title']
                except KeyError:
                    logger.warn("Can't find an article title in "+article[0])
                f.write(basename(newLocation)+'\t'+title+'\n')
    #Lets do some checks to see if we have enough stuff to stage and accession.
    if determineAlert(args):
        Alert("Accession me!")

    #The run is complete (and seems to have completed succesfully, write as much to the log.
    logger.info("Run complete.")

if __name__ == '__main__':
    main()
