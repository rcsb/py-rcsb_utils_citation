##
# File:    CitationReferenceProviderTests.py
# Author:  j. westbrook
# Date:    27-Apr-2019
# Version: 0.001
#
# Update:
##
"""
Test cases for citation reference information provider functions.

    @unittest.skipIf(condition, reason)
    @unittest.skipUnless(condition, reason)

"""

import logging
import os
import unittest

from rcsb.utils.citation.CitationReferenceProvider import CitationReferenceProvider

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class CitationReferenceProviderTests(unittest.TestCase):
    def setUp(self):
        self.__export = False
        self.__cachePath = os.path.join(HERE, "test-output", "cit_ref")

    def tearDown(self):
        pass

    def testGetJournalAbbrevs(self):
        """ Test get, cache and access citation reference journal abbreviations.
        """
        try:
            crP = CitationReferenceProvider(cachePath=self.__cachePath, useCache=False)
            ok = crP.testCache()
            self.assertTrue(ok)
            tD = {
                "journal_title": "Open journal of stomatology",
                "medline_abbrev": "Open J Stomatol",
                "issn_print": "2160-8709",
                "issn_online": "2160-8717",
                "iso_abbrev": "Open J Stomatol",
            }
            self.assertEqual(crP.getMedlineJournalIsoAbbreviation(tD["issn_print"]), tD["iso_abbrev"])
            self.assertEqual(crP.getMedlineJournalAbbreviation(tD["issn_print"]), tD["medline_abbrev"])
            self.assertEqual(crP.getMedlineJournalTitle(tD["issn_print"]), tD["journal_title"])
            self.assertEqual(crP.getMedlineJournalIsoAbbreviation(tD["issn_online"]), tD["iso_abbrev"])
            self.assertEqual(crP.getMedlineJournalAbbreviation(tD["issn_online"]), tD["medline_abbrev"])
            self.assertEqual(crP.getMedlineJournalTitle(tD["issn_online"]), tD["journal_title"])
            #
        except Exception as e:
            logger.exception("Failing with %s", str(e))
            self.fail()


def suiteCitationReferenceTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(CitationReferenceProviderTests("testGetJournalAbbrevs"))
    return suiteSelect


if __name__ == "__main__":
    #
    mySuite = suiteCitationReferenceTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
#
