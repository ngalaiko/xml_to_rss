from bs4 import BeautifulSoup
import time
import email.utils
xml = BeautifulSoup(open('../work/input.xml', 'r').read(), features = 'xml')
offer = xml.yml_catalog.offers.find_all('offer')[0]


print(email.utils.formatdate(time.mktime(time.gmtime(int(offer.modified_time.string)))))
