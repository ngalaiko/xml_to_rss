import ftplib
import time
from bs4 import BeautifulSoup

#ftp parameters
host = "galayko.netne.net"
ftp_user = "a8524605"
ftp_password = ""
filename = "./upload.xml"
time_to_sleep = 30
files_to_upload = 50
path_to_folder = '/test'

while True:
	#file to get items from
	source = BeautifulSoup(open('output.xml', 'r').read(), features = 'xml')
	#file to insert items to
	target = BeautifulSoup(open('start.xml', 'r').read(), features = 'xml')
	#if we have enough items
	if len(source.rss.channel.find_all('item')) < 50:
		sleep(time_to_sleep )
		continue
	#extracting item from sourse and inserting it to target X 50 times
	for i in range(files_to_upload):
		target.rss.channel.append(source.rss.channel.item.extract())
	#forming uploading file
	f = open('upload.xml', 'w')
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