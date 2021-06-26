import requests
from bs4 import BeautifulSoup
import re
import tempfile
import os
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import logging
from configurations.config import URL, extension, COLS, VALID_FILENAMES

logger = logging.getLogger()


class XmlParser():

    def __init__(self, url):
        self.url = url
        self.tempdir = tempfile.mkdtemp(prefix="xml_parser", suffix="zip_folder")

    def parsedownloadedlinks(self):

        # Request to pull the content from url
        xml_data = requests.get(self.url).content
        soup = BeautifulSoup(xml_data, "lxml")
        child = soup.find("result")

        ##Retrieve the downloaded links
        downloadlinks = child.find_all(attrs={'name': 'download_link'})
        return downloadlinks

    def retrievedownloadedlinks(self, download_links, file_names):
        ##creatine a list container
        urls_to_download_zip = []
        urlsregex = re.compile('http://\w*\.\w*\.\w*\.\w.\/\w*\/\w*\.\w*')
        for downlk in download_links:
            urls_to_download_zip.append(urlsregex.findall(str(downlk))[0])

        ## filter for links that have DLTINS
        urls_to_download_zip = list(filter(lambda x: bool(x.count(file_names)), urls_to_download_zip))

        # logger.info("The urls are "urls_to_download_zip)
        return urls_to_download_zip

    def downloadzippedfilesandextract(self, urls_to_download_zip):
        ##Dowloading the zipped files and extract them
        for xml_files in urls_to_download_zip:
            zip_filename = os.path.join(self.tempdir, xml_files.split("/")[-1])
            # download the file contents in binary format
            r = requests.get(xml_files)
            with open(zip_filename, "wb") as zip:
                zip.write(r.content)

        ##unzip the folders and remove the zipped folders
        os.chdir(self.tempdir)
        for item in os.listdir(self.tempdir):
            if item.endswith(extension):
                filename = os.path.abspath(self.tempdir + '\\' + item)
                zip_ref = zipfile.ZipFile(filename)
                zip_ref.extractall(self.tempdir)
                zip_ref.close()
                os.remove(filename)

    def xmlparsing_and_build_DataFrame(self, cols):
        ##Iterate through all the files
        df = None
        firstFileFlag = True
        for xml_files in os.listdir(self.tempdir):
            rows = []
            parsedfile = ET.parse(xml_files).getroot()
            maxrange = len(parsedfile[1][0][0])
            ##Now go through each loop and extract the fileds needed from each file.
            for start in range(1, maxrange):
                issr = parsedfile[1][0][0][start][0][1].text
                id = parsedfile[1][0][0][start][0][0][0].text
                fullName = parsedfile[1][0][0][start][0][0][1].text
                clsfctntp = parsedfile[1][0][0][start][0][0][3].text
                ntnlccy = parsedfile[1][0][0][start][0][0][4].text
                cmmdtyDerivInd = parsedfile[1][0][0][start][0][0][5].text
                rows.append([id, fullName, clsfctntp, cmmdtyDerivInd, ntnlccy, issr])
            ##Add the rows at each file to dataframe
            if firstFileFlag:
                df = pd.DataFrame(rows, columns=cols)
                firstFileFlag = False
            else:
                dataframe = pd.DataFrame(rows, columns=cols)
                df = df.append(dataframe, ignore_index=True)
        df = df[cols]
        return df
        logger.info("dataframe is successfully executed")

    def generateCsvFile(self, df):
        ##Convert the dataframe to csv as finaloutput
        ##TODO
        ##Not able to upload to s3 bucket as i donot have access.
        df.to_csv(self.tempdir + "\\finaldata.csv", index=False)


if __name__ == '__main__':
    try:
        xmlcsv = XmlParser(URL)
        links = xmlcsv.parsedownloadedlinks()
        downloaded_links = xmlcsv.retrievedownloadedlinks(links, VALID_FILENAMES)
        xmlcsv.downloadzippedfilesandextract(downloaded_links)
        data = xmlcsv.xmlparsing_and_build_DataFrame(COLS)
        xmlcsv.generateCsvFile(data)
    except Exception as e:
        logger.error("The program has failed with Error" + str(e))

