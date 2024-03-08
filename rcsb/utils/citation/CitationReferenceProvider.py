##
# File:    CitationReferenceProvider.py
# Date:    19-Nov-2019
#
# Updates:
# 21-Jul-2021 jdw  Make this provider a subclass of StashableBase
##

import copy
import logging
import os

from rcsb.utils.io.FileUtil import FileUtil
from rcsb.utils.io.MarshalUtil import MarshalUtil
from rcsb.utils.io.StashableBase import StashableBase

logger = logging.getLogger(__name__)


class CitationReferenceProvider(StashableBase):
    """Manage citation reference data access including resource files containing
    mapping between Journal names and ISSN/EISSN identifiers.  Provide accessors
    for searching these mappings.

    """

    def __init__(self, **kwargs):
        dirName = "citation-reference"
        cachePath = kwargs.get("cachePath", ".")
        super(CitationReferenceProvider, self).__init__(cachePath, [dirName])

        urlTargetCrossRef = kwargs.get("urlTargetCrossRef", "http://ftp.crossref.org/titlelist/titleFile.csv")
        urlTargetMedline = kwargs.get("urlTargetMedline", "https://ftp.ncbi.nlm.nih.gov/pubmed/J_Medline.txt")
        dirPath = os.path.join(cachePath, dirName)
        useCache = kwargs.get("useCache", True)
        #
        self.__mlIssnD, self.__crIssnD = self.__rebuildCache(urlTargetMedline, urlTargetCrossRef, dirPath, useCache)

    def getMedlineJournalIsoAbbreviation(self, issn):
        jAbbrev = None
        try:
            jAbbrev = self.__mlIssnD[issn]["iso_abbrev"]
        except Exception:
            pass
        return jAbbrev

    def getMedlineJournalAbbreviation(self, issn):
        jAbbrev = None
        try:
            jAbbrev = self.__mlIssnD[issn]["medline_abbrev"]
        except Exception:
            pass
        return jAbbrev

    def getMedlineJournalTitle(self, issn):
        jT = None
        try:
            jT = self.__mlIssnD[issn]["journal_title"]
        except Exception:
            pass
        return jT

    def getCrossRefJournalTitle(self, issn):
        jT = None
        try:
            jT = self.__crIssnD[issn]["journal_title"]
        except Exception:
            pass
        return jT

    def testCache(self):
        # Lengths ...
        logger.info("Lengths Medline %d CrossRef %d", len(self.__mlIssnD), len(self.__crIssnD))
        if (len(self.__mlIssnD) > 1000) and (len(self.__crIssnD) > 1000):
            return True
        return False

    #
    def __rebuildCache(self, urlTargetMedline, urlTargetCrossRef, cachePath, useCache):
        mlD = {}
        crD = {}
        mU = MarshalUtil(workPath=cachePath)
        fmt = "json"
        ext = fmt if fmt == "json" else "pic"
        medlineNamePath = os.path.join(cachePath, "medline-journals.%s" % ext)
        crossRefNamePath = os.path.join(cachePath, "crossref-journals.%s" % ext)
        #
        logger.debug("Using cache data path %s", cachePath)
        mU.mkdir(cachePath)
        if not useCache:
            for fp in [medlineNamePath, crossRefNamePath]:
                try:
                    os.remove(fp)
                except Exception:
                    pass
        #
        if useCache and mU.exists(medlineNamePath) and mU.exists(crossRefNamePath):
            mlD = mU.doImport(medlineNamePath, fmt=fmt)
            crD = mU.doImport(crossRefNamePath, fmt=fmt)
            logger.debug("Citation medline name length %d  CrossRef length %d", len(mlD), len(crD))
        elif not useCache:
            # ------
            fU = FileUtil()
            logger.info("Fetch data from source %s in %s", urlTargetMedline, cachePath)
            fp = os.path.join(cachePath, fU.getFileName(urlTargetMedline))
            ok = fU.get(urlTargetMedline, fp)
            mlD = self.__getMedlineJournalIndex(fp)
            ok = mU.doExport(medlineNamePath, mlD, fmt=fmt)
            logger.info("Caching %d Medline ISSNs in %s status %r", len(mlD), medlineNamePath, ok)
            # ------
            # CrossRef reference data -
            #   http://ftp.crossref.org/titlelist/titleFile.csv
            fp = os.path.join(cachePath, fU.getFileName(urlTargetCrossRef))
            ok = fU.get(urlTargetCrossRef, fp)
            crD = {}
            try:
                tDL = mU.doImport(fp, fmt="csv", rowFormat="dict")
                # crossref issn's are stripped of '-' and leading zeros.
                for tD in tDL:
                    tt = {}
                    for kyTup in [("JournalTitle", "journal_title"), ("pissn", "issn_print"), ("eissn", "issn_online"), ("doi", "doi")]:
                        if kyTup[0] in tD:
                            tt[kyTup[1]] = tD[kyTup[0]]
                    crD[tD["pissn"]] = tt
                    crD[tD["eissn"]] = tt
            except Exception as e:
                logger.exception("Failing processing %s in %s with %s", urlTargetCrossRef, fp, str(e))
            ok = mU.doExport(crossRefNamePath, crD, fmt=fmt)
            logger.info("Caching %d CrossRef ISSNs in %s status %r", len(crD), crossRefNamePath, ok)
            # ------
        #
        return mlD, crD

    def __getMedlineJournalIndex(self, filePath):
        """Parse Medline journal reference data and return a dictionary by ISSN

        Data from:
            ftp://ftp.ncbi.nih.gov/pubmed/J_Medline.txt

        Record format:
        --------------------------------------------------------
        JrId: 1
        JournalTitle: AADE editors' journal
        MedAbbr: AADE Ed J
        ISSN (Print): 0160-6999
        ISSN (Online):
        IsoAbbr: AADE Ed J
        NlmId: 7708172
        --------------------------------------------------------
        #
        """
        issnD = {}
        dD = {}
        with open(filePath, "r", encoding="utf-8") as ifh:
            for line in ifh:
                if "----" in line and "journal_title" in dD:
                    logger.debug("line %r: %r", line, dD)
                    if "issn_print" in dD:
                        issnD[dD["issn_print"]] = copy.copy(dD)
                    if "issn_online" in dD:
                        issnD[dD["issn_online"]] = copy.copy(dD)
                    dD = {}
                #
                fields = [f.strip() for f in line[:-1].split(":")]
                #
                tS = str(":".join(fields[1:])).strip() if len(fields) > 1 else ""
                if not tS:
                    continue
                if fields[0] == "JournalTitle":
                    dD["journal_title"] = tS
                if fields[0] == "IsoAbbr":
                    dD["iso_abbrev"] = tS
                if fields[0] == "MedAbbr":
                    dD["medline_abbrev"] = tS
                if fields[0] in ["ISSN (Print)"]:
                    dD["issn_print"] = tS
                if fields[0] in ["ISSN (Online)"]:
                    dD["issn_online"] = tS
        #
        logger.info("Medline ISSN journal length %d", len(issnD))
        return issnD
