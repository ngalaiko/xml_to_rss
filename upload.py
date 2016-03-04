import ftplib
import time
from bs4 import BeautifulSoup

#ftp parameters
host = "agency.dev.e-generator.ru"
ftp_user = ""
ftp_password = ""
filename = "./sale_rss.xml"
time_to_sleep = 60 *60 #in sec
items_to_upload = 75
path_to_folder = '/s.egenerator.ru'

#var for new number of items if we have less than items_to_upload
n = items_to_upload

while True:
	#file to get items from
	source = BeautifulSoup(open('output.xml', 'r').read(), features = 'xml')
	#file to insert items to
	target = BeautifulSoup(open('start.xml', 'r').read(), features = 'xml')
	#if we have no items at all
	if len(source.rss.channel.find_all('item')) == 0:
		time.sleep(1)
		continue
	#if we have some items, change number of items to upload
	if len(source.rss.channel.find_all('item')) < items_to_upload:
		n = len(source.rss.channel.find_all('item'))
	#extracting item from sourse and inserting it to target X 50 times
	for i in range(n):
		target.rss.channel.append(source.rss.channel.item.extract())
	#make needed items number again
	n = items_to_upload
	#forming uploading file
	f = open(filename, 'w')
	f.write(target.prettify())
	f.close()
	#sending it
	#open connection
	con = ftplib.FTP(host, ftp_user, ftp_password)
	#go to target folder
	con.cwd(path_to_folder)
	#open file to transfer in binary mode
	f = open(filename, "rb")
	#trensfer
	send = con.storbinary("STOR "+ filename, f)
	#close connection and file
	f.close()
	con.close
	#appending changes to source file
	f = open('output.xml', 'w')
	f.write(source.prettify())
	f.close()
	#and wait
	time.sleep(time_to_sleep)