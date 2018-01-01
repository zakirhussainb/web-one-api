'''
File        : extract_utils
Description : This will contain the utility functions that can be reused
              across the different extractors.
'''

import json
import logging
import os
import re
from urllib.parse import urljoin

import tldextract
import yaml
from fuzzywuzzy import fuzz

logger = logging.getLogger()

# Read the Keywords/Config from keywords.yaml
with open(os.path.join(os.path.dirname(__file__), "keywords.yaml"), 'r') as ymlFile:
    keywordsMap = yaml.load(ymlFile)

'''
Function    : handlesException
Description : This is to be used as a Decorator to handle exceptions
              gracefully
@:param     : function object
@:returns   : function object
'''


def handlesException(inp_func):
    def wrap_func(*args, **kwds):
        try:
            result = inp_func(*args, **kwds)
            return (None, result)
        except Exception as e:
            result = str(e)
            return (1, result)

    return wrap_func


'''
Function    : toNum
Description : This will convert the given string to number by removing all
              non-numeric characters.
@:param     : st - String containing numeric characters
@:returns   : String with only numeric characters present , which can then
              be casted to any numeric value (int or float)
'''


def toNum(st):
    num_regex = r"([^0-9.])+"
    result = re.sub(num_regex, "", st)
    if result:
        return result
    else:
        return st


'''
Function    : toFloat
Description : This will cast the given string or number to float format.
@:param     : String that can be casted to Float easily
@:returns   : Float number if casting was successful , else -1
'''


def toFloat(num):
    try:
        result = float(num)
    except Exception as e:
        logger.error(str(e))
        logger.exception('toFloat error')
        result = -1
    return result


'''
Function    : toInt
Description : This will cast the given string or number to int format.
@:param     : String that can be casted to Integer easily
@:returns   : Integer number if casting was successful , else -1
'''


def toInt(num):
    try:
        result = int(num)
    except Exception as e:
        logger.error(str(e))
        logger.exception('toInt error')
        result = -1
    return result


'''
Function    : cleanText
Description : This will clean the text by stripping of empty spaces and also will
              escape single quotes.
              This escaping is primarily for easier Exporting to Postgres.
@:param     : st- Text to be cleaned
@:return    : Cleaned Text
'''


def cleanText(st):
    try:
        return st.strip().replace("'", "''")
    except Exception as e:
        logger.error(str(e))
        logger.exception('cleanText error')
        return st


'''
Function    : cleanLinks
Description : This is specific to SimilarTech Source , where it will return
              the contents if present after the last '/'
@:param     : link
@:return    : cleaned data
'''


def cleanLinks(link):
    try:
        return link[link.rfind('/') + 1:]
    except Exception as e:
        logger.error(str(e))
        logger.exception('cleanLinks error')
        return None


'''
Function    : extractFirst
Description : This will extract the data if present. It will also cleanup by
              removing extra spaces and so on .
@:param     : val - Element as provided by BeautifulSoup
@:return    : Cleaned Text - if val is a Element Node
              As it is - if val is present and itself a text
              '' - If any exception
'''


def extractFirst(val):
    try:
        if val:
            # Strip out extra characters
            val = val.text.strip()
            # Remove newlines and other extra spaces like \t,\r
            val = val.replace("\t", " ").replace("\r", " ").replace("\n", " ")
            return val
        if val:
            return val
        return ''
    except AttributeError as e:
        logger.error(str(e))
        logger.exception('extractFirst error')
        return val
    except Exception as e:
        logger.error(str(e))
        logger.exception('extractFirst error')
        return ''


'''
Function    : extractTextAsIs
Description : This will extract the Text as is without any cleansing
@:param     : val - Soup Element
@:return    : text - that was extracted if success
              None - otherwise
'''


def extractTextAsIs(val):
    try:
        val = val.text
        return val
    except Exception as e:
        logger.error(str(e))
        logger.exception('extractTextAsIs error')
        return None


'''
Function    : extractAttributeValue
Description : This will extract the Attribute Value if present
@:param     : tag - Tag whose attribute is to be extracted
              attr - attribute whose value is to be extracted
@:returns   : val - Value of the Attribute if present
              '' , otherwise
'''


def extractAttributeValue(tag, attr):
    val = ""
    try:
        val = tag[attr]
    except Exception as e:
        logger.error(str(e))
        logger.exception('extractAttributeValue error')
        val = ''
    return val


'''
Function    : toAbsoluteURL
Description : This will merge the given url with the base url .
              Useful for getting absolute urls given relative url.
@:params    : base_url - Base URL
              url - Relative url which is to be transformed to Absolute URL
@:returns   : Absolute URL
'''


def toAbsoluteURL(base_url, url):
    '''
    :param url:
    :param base_url:
    :return:
    '''
    try:
        return urljoin(base_url, url)
    except Exception as e:
        logger.error(str(e))
        logger.exception('toAbsoluteURL error')
        return url


'''
Function        : isEmailLink
Description     : Checks if the given Link is an Email Address or not
@:param         : url
@:return        : True if url is Email Link,
                  False otherwise
'''


def isEmailLink(url):
    try:
        if "mailto:" in url.lower():
            return True
        res = mailValidation.email(url)
        return res
    except Exception as e:
        logger.error(str(e))
        logger.exception('isEmailLink error')
        return False


'''
Function    : isSocialLink
Description : Checks if the given Link or URL is a Social Link or not
@:param     : url
@:return    : True if url is Social Link ,
              False otherwise
'''


def isSocialLink(url):
    sociallink_domains = frozenset(
        ['linkedin', 'facebook', 'twitter', 'youtube', 'instagram', 'pinterest', 'plus_google'])
    try:
        url_ext = tldextract.extract(url)
        url_domain = url_ext.domain.lower()
        url_subdomain = url_ext.subdomain.lower()
        if url_domain in keywordsMap['social_links']:
            return True
        # Checking if its Google Plus
        elif ('{}_{}'.format(url_subdomain, url_domain)) in keywordsMap['social_links']:
            return True
        else:
            return False
    except Exception as e:
        logger.error(str(e))
        logger.exception('isSocialLink error')
        return False


'''
Function    : isDomainLink
Description : This will check if the link is of the same domain as the root link
@:param     : root , url
@:return    : True if Same Domain,
              False,otherwise
'''


def isDomainLink(root, url):
    try:

        root_domain = tldextract.extract(root).domain
        child_domain = tldextract.extract(url).domain
        matchRatio = fuzz.ratio(root_domain, child_domain)

        fuzzThreshold = int(keywordsMap['inlink_threshold'])

        # Log the ration if falls below threshold by a small margin
        # This is to analyze if we need to reduce the threshold or not
        # if (fuzzThreshold - 5) <= matchRatio <= fuzzThreshold:
        #    self.logger.info('Match Ratio : {} || {} : {}'.format(root,url,matchRatio))

        if matchRatio >= fuzzThreshold:
            return True
        else:
            return False
    except Exception as e:
        logger.error(str(e))
        logger.exception('isDomainLink error')
        return False


'''
Function    : saveToFile
Description : This will save the extracted Data to a file locally
@:param     : extData - Dict that is to be stored
              outFileName - File Name under which to save
              format - Format to be stored in the File
@:returns   : Absolute File Path of the File generated
'''


def saveToFile(extData, outFileName, outFormat='json'):
    baseDir = '/tmp/extraction/output/'
    os.makedirs(baseDir, exist_ok=True)
    outFilePath = os.path.join(baseDir, '{}.{}'.format(outFileName, outFormat))
    if outFormat == 'json':
        with open(outFilePath, 'w') as fout:
            json.dump(extData, fout)
        return outFilePath