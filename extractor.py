"""
File        : extractor_for_generic
Description : This contains the Extraction Logic/Rules to be used for
              Generic/Default Source
"""
import logging
import utils as eutil
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger()

logger.setLevel(level="INFO")

logging.info("extractor initialized")

'''
Function    : extract
Description : This will extract the required information from the given
              raw_html file and return data found.
@:param     : inpFileKey - File Key/Name under which to save
              inpFile - Path to file containing raw_html
              inpBinObj - Binary File Object containing raw_html
              url - URL for which inpFile contains the raw_html
              format - Format to be used to store the extracted data in the file
@:returns   : Dict - containing the Extracted Data
'''


def extract(url, inpBinObj, outFormat='json'):
    logger.info('extraction started')
    logger.info('url : {}'.format(url))
    soup = BeautifulSoup(inpBinObj, "html.parser")
    header = {}
    body = {}
    next_url = []

    # Populate the Header portion with relevant information
    header['url'] = url
    # Set the Extracted Timestamp
    header['extracted_ts'] = str(datetime.utcnow())
    # Set Status Code and Status Msg
    header['status_code'] = 200
    header['status_msg'] = 'OK'

    # Check if Soup is present or not
    if soup:
        # Extracting the title
        body['title'] = eutil.extractFirst(soup.find("title"))

        # Extract the Detected Encoding
        body['encoded_in'] = eutil.extractFirst(soup.original_encoding)

        # Extracting the SEO Data
        body['seo'] = getSEOData(soup)

        # Extract the Images Tag Data
        body['images'] = getImageTags(soup)

        # Extract the Scripts Tag Data
        body['scripts'] = getScriptTags(soup)

        # Remove Script and Style Tags if present
        for tag in soup.find_all("script"):
            tag.extract()
        for tag in soup.find_all("style"):
            tag.extract()

        # Extract the Meta Tag Data
        body["meta"] = getMetaData(soup)

        # Extract the Links
        body['links'] = getLinks(soup, url)

        # Store the Raw Text Extracted
        body['raw_text'] = soup.get_text()

    else:
        header['status_code'] = 999
        header['status_msg'] = 'Could not generate the soup . Raw HTML might be empty'
        logger.error('raw html is either missing or empty')

    webdata = {}
    webdata['header'] = header
    webdata['body'] = body

    logger.info('extraction completed')

    logger.info('generating output file : started')
    logger.info('generating output file : completed')
    logger.info('--------------------')
    return webdata


'''
Function    : getLinks
Description : This will extract the Links present
@:param     : isoup - Soup Object
              baseURL - Base URL under consideration
@:return    : Dict - Dict containing the links along with other info.
              Empty Dict , otherwise
'''


def getLinks(isoup, baseURL):
    logger.info('links extraction : started')
    inlinks = []
    outlinks = []
    sociallinks = []
    emails = []

    for link in isoup.find_all('a'):

        # <a href="" id="" name="">atext</a>
        href = eutil.extractAttributeValue(link, 'href')
        aid = eutil.extractAttributeValue(link, "id")
        aname = eutil.extractAttributeValue(link, "name")
        atext = eutil.extractFirst(link)

        # Convert href to Absolute if its relative
        href = eutil.toAbsoluteURL(base_url=baseURL, url=href)

        # Create a KV Pair for the Link
        kv = {}
        kv['href'] = href
        kv['aid'] = aid
        kv['aname'] = aname
        kv['atext'] = atext

        # Check if the Link is Email Link or not
        if eutil.isEmailLink(href):
            emails.append(kv)

        # Check If Link is a Social Link or not
        elif eutil.isSocialLink(href):
            sociallinks.append(kv)

        # Check if Link is an Inlink or not
        elif eutil.isDomainLink(baseURL, href):
            inlinks.append(kv)

        # Check if Link is an Outlink or not
        else:
            outlinks.append(kv)

    result = {}
    result['emails'] = emails
    result['sociallinks'] = sociallinks
    result['inlinks'] = inlinks
    result['outlinks'] = outlinks

    logger.info('links extraction : completed')
    return result


'''
Function    : getScriptTags
Description : This will extract all Script related Tag Information
@:param     : isoup - Soup Object
@:return    : List - List of Dict where each dict contains info of a
              single Script Tag if present
              Empty List, otherwise
'''


def getScriptTags(isoup):
    logger.info('scripts extraction : started')
    scripts = []
    for sc in isoup.find_all('script'):
        kv = {}
        kv['script_src'] = sc.get('src')
        kv['script_type'] = sc.get('type', "")
        if kv['script_src']:
            scripts.append(kv)
    logger.info('scripts extraction : completed')
    return scripts


'''
Function    : getImageTags
Description : This will extract all Image related Tag Information
@:param     : isoup - Soup Object
@:returns   : List - List of Dict where each dict contains info of a
              single Image Tag if present
              Empty List , otherwise
'''


def getImageTags(isoup):
    logger.info('images extraction : started')
    images = []
    for img in isoup.find_all('img'):
        kv = {}
        kv['img_src'] = img.get('src')
        kv['img_alt'] = img.get('alt', "")
        if kv['img_src']:
            images.append(kv)
    logger.info('images extraction : completed')
    return images


'''
Function    : getMetaData
Description : This will get the data present within the meta tag
              <meta> ... </meta>
@:param     : soup - Soup Object
@:return    : List - List of Dict where each Dict contains info of a
              single meta tag
'''


def getMetaData(isoup):
    logger.info('metadata extraction : started')
    metaData = []
    for tag in isoup.find_all("meta"):
        # Get the attributes dictionary
        attrDict = tag.attrs
        if attrDict:
            metaData.append(attrDict)
    logger.info('metadata extraction : completed')
    return metaData


'''
Function    : getSEOData
Description : This will get the SEO data which normally appears in the
              format : <script type="application/ld+json"> ... </script>
@:param     : soup - Soup Object from which to extract
@:returns   : List - List of Dicts containing the SEO Data if present
              Empty List otherwise
'''


def getSEOData(isoup):
    logger.info('seo extraction : started')
    seoDataList = []

    for item in isoup.find_all("script", attrs={"type": "application/ld+json"}):
        seoDataList.append(eutil.extractTextAsIs(item))
    logger.info('seo extraction : completed')
    return seoDataList


def normalize_url(url=None):
    if not url:
        return None
    elif url.startswith('http://www.'):
        return url[11:]
    elif url.startswith('https://www.'):
        return url[12:]
    elif url.startswith('https://'):
        return url[8:]
    elif url.startswith('www.'):
        return url[4:]
    else:
        return url
