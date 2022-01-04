##
# File:    JournalTitleAbbreviationProviderTests.py
# Author:  j. westbrook
# Date:    27-Apr-2019
# Version: 0.001
#
# Update:
##
"""
Test cases for journal title abbreviation provider
"""

import logging
import os
import unittest

import nltk

from rcsb.utils.citation.JournalTitleAbbreviationProvider import JournalTitleAbbreviationProvider

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class JournalTitleAbbreviationProviderTests(unittest.TestCase):
    def setUp(self):
        self.__export = False
        self.__cachePath = os.path.join(HERE, "test-output", "CACHE")
        nltk.download("wordnet")
        nltk.download("omw-1.4")

    def tearDown(self):
        pass

    def testGetJournalAbbrevs(self):
        """Test get, cache and access resources support journal title abbreviation methods"""
        try:
            crP = JournalTitleAbbreviationProvider(cachePath=self.__cachePath, useCache=False)
            ok = crP.testCache()
            self.assertTrue(ok)
            tD = {
                "journal_title": "Open Journal of Stomatology",
                "medline_abbrev": "Open J Stomatol",
                "issn_print": "2160-8709",
                "issn_online": "2160-8717",
                "iso_abbrev": "Open J Stomatol",
            }
            logger.debug("abbreviation %r", crP.getJournalAbbreviation(tD["journal_title"], usePunctuation=True))
            logger.debug("abbreviation %r", crP.getJournalAbbreviation(tD["journal_title"], usePunctuation=False))
            self.assertEqual(crP.getJournalAbbreviation(tD["journal_title"], usePunctuation=False), tD["iso_abbrev"])
            #
        except Exception as e:
            logger.exception("Failing with %s", str(e))
            self.fail()


def suiteIsoAbbreviationTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(JournalTitleAbbreviationProviderTests("testGetJournalAbbrevs"))
    return suiteSelect


if __name__ == "__main__":
    #
    mySuite = suiteIsoAbbreviationTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
#
