import unittest
import tempfile
import os
import re
from configurations.config import URL, COLS, VALID_FILENAMES
from src.xml_parser import XmlParser

class XmlParserUnitTest(unittest.TestCase):
    def setUp(self):
        self.x = XmlParser(URL)
        self.x.tempdir = tempfile.mkdtemp(prefix="test_xml_parser", suffix="zip_folder")

    def test_xml_to_csv(self):
        downlinks = self.x.parsedownloadedlinks()
        self.matchpattern(downlinks,'download_link')

        ##Adding an extra link to check it is filtering for only DLTINS
        downlinks.append('<str name="download_link">http://firds.esma.europa.eu/firds/xyz_20210117_01of01.zip</str>')
        zipfiles = self.x.retrievedownloadedlinks(downlinks, VALID_FILENAMES)
        self.matchpattern(zipfiles, VALID_FILENAMES)

        ##Testing the xml files in the folder.
        self.x.downloadzippedfilesandextract(zipfiles)
        extractedfiles =  os.listdir(self.x.tempdir)
        self.matchpattern(extractedfiles, 'xml')

        ##Retrieve the DatFrame from the parsed xml
        dataFrame = self.x.xmlparsing_and_build_DataFrame(COLS)
        self.assertEqual(list(dataFrame),COLS)
        self.assertTrue(len(dataFrame))

        ##checking the xml is in csv file

    def matchpattern(self,input,text):
        for lnk in input:
            self.assertTrue(re.search(text,str(lnk)))


if __name__ == '__main__':
    unittest.main()
