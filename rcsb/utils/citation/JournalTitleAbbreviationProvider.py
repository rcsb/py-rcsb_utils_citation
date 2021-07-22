##
# File:    JournalTitleAbbreviationProvider.py
# Date:    20-Nov-2019 J. Westbrook
#
##


import logging
import os
import string
import unicodedata

import regex as re
from nltk.stem.wordnet import WordNetLemmatizer

from rcsb.utils.io.FileUtil import FileUtil
from rcsb.utils.io.MarshalUtil import MarshalUtil
from rcsb.utils.io.StashableBase import StashableBase

logger = logging.getLogger(__name__)


class JournalTitleAbbreviationProvider(StashableBase):
    """Manage resources required to support journal title abbreviation assignment
    using ISO LTWA abbreviations at:

      https://www.issn.org/services/online-services/access-to-the-ltwa/

    Portions of this module have been adapted from the approach developed
    in https://github.com/adlpr/iso4.git with the following license:

        MIT License

        Copyright (c) 2018 Alex DelPriore

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.
    """

    def __init__(self, **kwargs):
        dirName = "journal-abbreviations"
        cachePath = kwargs.get("cachePath", ".")
        super(JournalTitleAbbreviationProvider, self).__init__(cachePath, [dirName])
        urlTargetIsoLtwa = kwargs.get("urlTargetLtwa", "https://www.issn.org/wp-content/uploads/2013/09/LTWA_20160915.txt")
        dirPath = os.path.join(cachePath, dirName)
        useCache = kwargs.get("useCache", True)
        #
        self.__noAbbrevPlaceHolder = "n.a."
        self.__prefixKey = "prefix"
        self.__suffixKey = "suffix"
        self.__infixKey = "infix"
        self.__fullWordKey = "full"
        self.__lowercaseFlag = "lower"
        self.__uppercaseFlag = "upper"
        self.__titlecaseFlag = "title"
        #
        self.__wml = WordNetLemmatizer()
        #
        self.__stopWords = set(
            [
                "a",
                "about",
                "afore",
                "after",
                "ago",
                "along",
                "amid",
                "among",
                "amongst",
                "an",
                "and",
                "apropos",
                "as",
                "at",
                "atop",
                "but",
                "by",
                "ca",
                "circa",
                "for",
                "from",
                "hence",
                "in",
                "into",
                "like",
                "nor",
                "of",
                "off",
                "on",
                "onto",
                "ontop",
                "or",
                "out",
                "over",
                "per",
                "since",
                "so",
                "than",
                "the",
                "though",
                "til",
                "till",
                "to",
                "unlike",
                "until",
                "unto",
                "up",
                "upon",
                "upside",
                "versus",
                "via",
                "vis-a-vis",
                "vs",
                "when",
                "whenever",
                "where",
                "whereas",
                "wherever",
                "while",
                "with",
                "within",
                "yet",
                "aus",
                "des",
                "der",
                "für",
                "im",
                "und",
                "zu",
                "zur",
                "da",
                "de",
                "del",
                "della",
                "delle",
                "di",
                "do",
                "e",
                "el",
                "en",
                "et",
                "i",
                "la",
                "le",
                "lo",
                "las",
                "les",
                "los",
                "y",
                "van",
                "voor",
                "og",
            ]
        )
        self.__abbrevD, self.__conflictD, self.__multiWordTermList = self.__rebuildCache(urlTargetIsoLtwa, dirPath, useCache)
        # Token a string space boundaries respecting a special list of multi-word strings -
        self.__tokenizerRegex = re.compile("({}|\\s+)".format("|".join(["(?:^|\\s){}(?:\\s|$)".format(w) for w in self.__multiWordTermList])), flags=re.I)

    def testCache(self):
        # Lengths ...
        try:
            logger.info("Abbreviation length LTWA %d", len(self.__abbrevD["full"]))
            if len(self.__abbrevD) == 4 and len(self.__abbrevD["full"]) > 39000 and len(self.__multiWordTermList) > 250:
                return True
        except Exception:
            pass
        return False

    def __rebuildCache(self, urlTargetIsoLtwa, dirPath, useCache):
        """Rebuild the cache of ISO abbreviation term data

        Args:
            urlTargetIsoLtwa (str): URL for ISO4 LTWA title word abbreviations
            dirPath (str):  cache path
            useCache (bool):  flag to use cached files

        Returns:
            tuple: (dict) title word abbreviations
                   (dict) language conflict dictionary
                   (list) multi-word abbreviation targets

        Notes:
            ISO source file (tab delimited UTF-16LE) is maintained at the ISSN site -
            https://www.issn.org/wp-content/uploads/2013/09/LTWA_20160915.txt
        """
        aD = {}
        mU = MarshalUtil(workPath=dirPath)
        fmt = "json"
        ext = fmt if fmt == "json" else "pic"
        isoLtwaNamePath = os.path.join(dirPath, "iso-ltwa.%s" % ext)
        logger.debug("Using cache data path %s", dirPath)
        mU.mkdir(dirPath)
        if not useCache:
            for fp in [isoLtwaNamePath]:
                try:
                    os.remove(fp)
                except Exception:
                    pass
        #
        if useCache and mU.exists(isoLtwaNamePath):
            aD = mU.doImport(isoLtwaNamePath, fmt=fmt)
            logger.debug("Abbreviation name length %d", len(aD["abbrev"]))
        elif not useCache:
            # ------
            fU = FileUtil()
            logger.info("Fetch data from source %s in %s", urlTargetIsoLtwa, dirPath)
            fp = os.path.join(dirPath, fU.getFileName(urlTargetIsoLtwa))
            ok = fU.get(urlTargetIsoLtwa, fp)
            aD = self.__getLtwaTerms(dirPath, fp)
            ok = mU.doExport(isoLtwaNamePath, aD, fmt=fmt)
            logger.debug("abbrevD keys %r", list(aD.keys()))
            logger.debug("Caching %d ISO LTWA in %s status %r", len(aD["abbrev"]), isoLtwaNamePath, ok)
        #
        abbrevD = aD["abbrev"] if "abbrev" in aD else {}
        conflictD = aD["conflicts"] if "conflicts" in aD else {}
        multiWordTermL = aD["multi_word_abbrev"] if "multi_word_abbrev" in aD else []
        #
        return abbrevD, conflictD, multiWordTermL

    def getJournalAbbreviation(self, title, usePunctuation=True):
        #
        useLangs = ["eng"]
        title = unicodedata.normalize("NFKD", title)
        useLangs = set(useLangs)

        # split title either at space on as defined as multi-word targets
        titleWords = list(filter(lambda w: w.strip(), self.__tokenizerRegex.split(title)))

        retWordList = []

        # Exception for single-word titles
        if len(titleWords) == 1 and len(titleWords[0].split(" ")) == 1:
            return title

        for origWord in titleWords:
            # normalize and lemmatize
            wordNorm = self.__normalizeWord(origWord)

            # skip stopwords
            if wordNorm in self.__stopWords:
                continue

            # if normalized word fails, try lemma
            wordLemma = self.__wml.lemmatize(wordNorm)
            wordCandidates = (wordNorm, wordLemma) if wordNorm != wordLemma else (wordNorm,)

            wordAbbr = ""
            capitalization = self.__getCapitalization(origWord)

            for word in wordCandidates:
                # Check for language degeneracy in mapping
                if self.__fullWordKey in self.__conflictD and word in self.__conflictD[self.__fullWordKey]:
                    allowedLangs = self.__conflictD[self.__fullWordKey][word].keys()
                    possibleLangs = allowedLangs & useLangs
                    if len(possibleLangs) == 1:
                        wordAbbr = self.__conflictD[self.__fullWordKey][word][possibleLangs.pop()]
                        break
                    else:
                        logger.error("Language mapping conflict for term %r (%r)", word, allowedLangs)
                        return title
                if not wordAbbr and self.__prefixKey in self.__conflictD:
                    # prefix conflicts
                    for prefix in sorted(self.__conflictD[self.__prefixKey].keys()):
                        if word.startswith(prefix):
                            allowedLangs = self.__conflictD[self.__prefixKey][word].keys()
                            possibleLangs = allowedLangs & useLangs
                            if len(possibleLangs) == 1:
                                wordAbbr = self.__conflictD[self.__prefixKey][word][possibleLangs.pop()]
                            else:
                                logger.error("Language mapping conflict for term %r (%r)", word, allowedLangs)
                                return title

                if not wordAbbr and self.__suffixKey in self.__conflictD:
                    # suffix conflicts
                    for suffix in sorted(self.__conflictD[self.__suffixKey].keys()):
                        if word.endswith(suffix):
                            allowedLangs = self.__conflictD[self.__suffixKey][word].keys()
                            possibleLangs = allowedLangs & useLangs
                            if len(possibleLangs) == 1:
                                wordAbbr = self.__conflictD[self.__suffixKey][word][possibleLangs.pop()]
                            else:
                                logger.error("Language mapping conflict for term %r (%r)", word, allowedLangs)
                                return title

                if not wordAbbr and self.__infixKey in self.__conflictD:
                    # infix conflicts
                    for infix in sorted(self.__conflictD[self.__infixKey].keys()):
                        if infix in word:
                            allowedLangs = self.__conflictD[self.__infixKey][word].keys()
                            possibleLangs = allowedLangs & useLangs
                            if len(possibleLangs) == 1:
                                wordAbbr = self.__conflictD[self.__infixKey][word][possibleLangs.pop()]
                            else:
                                logger.error("Language mapping conflict for term %r (%r)", word, allowedLangs)
                                return title
                if wordAbbr:
                    break

                # Evaluate abbreviation mapping for each word type
                if not wordAbbr and self.__fullWordKey in self.__abbrevD and word in self.__abbrevD[self.__fullWordKey]:
                    wordAbbr = self.__abbrevD[self.__fullWordKey][word]
                    break
                if not wordAbbr and self.__prefixKey in self.__abbrevD:
                    # check prefixes in descending length order
                    for prefix in sorted(self.__abbrevD[self.__prefixKey].keys(), key=lambda p: (-len(p), p)):
                        if word.startswith(prefix):
                            wordAbbr = self.__abbrevD[self.__prefixKey][prefix]
                            break
                if not wordAbbr and self.__suffixKey in self.__abbrevD:
                    # check suffixes in descending length order
                    for suffix in sorted(self.__abbrevD[self.__suffixKey].keys(), key=lambda p: (-len(p), p)):
                        if word.endswith(suffix):
                            wordAbbr = self.__abbrevD[self.__suffixKey][suffix]
                            break
                if not wordAbbr and self.__infixKey in self.__abbrevD:
                    # check infixes in descending length order
                    for infix in sorted(self.__abbrevD[self.__infixKey].keys(), key=lambda p: (-len(p), p)):
                        if infix in word:
                            wordAbbr = self.__abbrevD[self.__infixKey][infix]
                            break
                if wordAbbr:
                    break

            # Apply formating preferences
            if wordAbbr in ("", self.__noAbbrevPlaceHolder):
                wordAbbr = self.__finalizeOutput(word, capitalization, usePunctuation=False)
            else:
                wordAbbr = self.__finalizeOutput(wordAbbr, capitalization, usePunctuation)

            retWordList.append(wordAbbr)
        return unicodedata.normalize("NFKC", " ".join(retWordList))

    def __getType(self, word):
        """Classify the input word base on internal punctuation."""
        if word.startswith("-"):
            return self.__infixKey if word.endswith("-") else self.__suffixKey
        elif word.endswith("-"):
            return self.__prefixKey
        else:
            return self.__fullWordKey

    def __getCapitalization(self, word):
        """Classify case construction of the input term.

        Args:
            word (str): Input term to be evaluated

        Returns:
            (str): flag indicating case ('upper', 'lower', 'title')
        """
        if word == word.upper():
            return self.__uppercaseFlag
        elif word[0].isupper():
            # guess title case if not all upper
            return self.__titlecaseFlag
        else:
            return self.__lowercaseFlag

    def __normalizeWord(self, word):
        """Strip hyphens, other punctuation, lower, normalize NFKD."""
        parts = []
        for part in word.split(" "):
            part = re.sub(r"(^\-|\p{P}+$)", "", part).strip()
            parts.append(unicodedata.normalize("NFKD", part.lower()))
        return " ".join(parts).strip()

    def __normalizeAbbr(self, abbr):
        """Strip hyphens, period, lower, normalize NFKD (if not "n.a.")."""
        if abbr == self.__noAbbrevPlaceHolder:
            return abbr
        parts = []
        for part in abbr.split(" "):
            parts.append(unicodedata.normalize("NFKD", part.strip("- ").rstrip(".").lower()))
        return " ".join(parts)

    def __finalizeOutput(self, word, capitalization, usePunctuation):
        """Modify output word according to capitalization and punctuation preferences."""
        parts = []
        for part in word.split(" "):
            if capitalization == self.__uppercaseFlag:
                part = part.upper()
            elif capitalization == self.__titlecaseFlag:
                part = string.capwords(part)
            if usePunctuation:
                part += "."
            parts.append(part)
        return " ".join(parts)

    def __getLtwaTerms(self, dirPath, isoLtwaNamePath):
        logger.info("Processing terms in %r", isoLtwaNamePath)
        titleWordAbbrevD = {}
        conflictD = {}
        multiWordTermL = []
        abbrevD = {"abbrev": titleWordAbbrevD, "conflicts": conflictD, "multi_word_abbrev": multiWordTermL}
        #
        mU = MarshalUtil(workPath=dirPath)
        try:
            tsv = mU.doImport(isoLtwaNamePath, fmt="tdd", rowFormat="list", encoding="utf-16-le")
            logger.debug("Read isoLtwaNamePath %s record count %d", isoLtwaNamePath, len(tsv))
            conflictWords = set()
            for line in tsv:
                try:
                    if len(line) == 3:
                        word, abbr, langs = line
                    else:
                        word, abbr = line
                        langs = ""

                except Exception:
                    logger.error("Format issue for line %r", line)
                    continue
                wType = self.__getType(word)
                word = self.__normalizeWord(word)
                abbr = self.__normalizeAbbr(abbr)
                # Assign word type -
                if wType not in titleWordAbbrevD:
                    titleWordAbbrevD[wType] = {}
                # Detect conflict words
                if word in titleWordAbbrevD[wType]:
                    conflictWords.add((wType, word))
                elif " " in word:
                    multiWordTermL.append(re.escape(word))
                #
                titleWordAbbrevD[wType][word] = abbr
            # Build dictionary capturing degenerate language specific mappings
            for wType, word in conflictWords:
                # remove from main list
                titleWordAbbrevD[wType].pop(word)
            logger.debug("conflict words length %d", len(conflictWords))
            for line in tsv:
                try:
                    if len(line) == 3:
                        word, abbr, langs = line
                    else:
                        word, abbr = line
                        langs = ""
                except Exception:
                    logger.error("Format issue for line %r", line)
                    continue
                wType = self.__getType(word)
                word = self.__normalizeWord(word)
                logger.debug("Word %r wordType %r", word, wType)
                if (wType, word) in conflictWords:
                    abbr = self.__normalizeAbbr(abbr)
                    if wType not in conflictD:
                        conflictD[wType] = {}
                    if word not in conflictD[wType]:
                        conflictD[wType][word] = {}
                    for lang in langs.split(","):
                        conflictD[wType][word][lang.strip()] = abbr
            multiWordTermL = sorted(list(set(multiWordTermL)))
            #
            abbrevD = {"abbrev": titleWordAbbrevD, "conflicts": conflictD, "multi_word_abbrev": multiWordTermL}
            for ky in abbrevD["abbrev"]:
                logger.debug("abbreviation type %r length %r", ky, len(abbrevD["abbrev"][ky]))
            for ky in abbrevD:
                logger.debug("Content type %r length %r", ky, len(abbrevD[ky]))
            #
        except Exception as e:
            logger.exception("Failing reading %s with %s", isoLtwaNamePath, str(e))

        return abbrevD
