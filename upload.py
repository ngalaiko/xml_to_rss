import ftplib
import time
from bs4 import BeautifulSoup
import sys
import argparse

def create_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument('-ftp_host', default = None)
	parser.add_argument('-user', default = None)
	parser.add_argument('-password', default = None)
	parser.add_argument('-time', default = None)
	parser.add_argument('-items', default = None)
	parser.add_argument('-path', default = None)
	parser.add_argument('-filename', default = None)

	return parser

if __name__ == '__main__':
	#creating parser to get arguments
	parser = create_parser()
	namespace = parser.parse_args(sys.argv[1:])
	
	if not namespace.ftp_host and not namespace.user and not namespace.password and not namespace.filename and not namespace.time and not namespace.items and not namespace.path:
			sys.exit()

	#print(namespace)

	#ftp parameters
	host = namespace.ftp_host
	ftp_user = namespace.user
	ftp_password = namespace.password
	filename = namespace.filename
	time_to_sleep = int(namespace.time)
	items_to_upload = int(namespace.items)
	path_to_folder = namespace.path

	#var for new number of items if we have less than items_to_upload
	n = items_to_upload

	while True:
		#file to get items from
		source = BeautifulSoup(open('output.xml', 'r').read(), features = 'xml')
		#file to insert items to
		target = BeautifulSoup(open('start.xml', 'r').read(), features = 'xml')
		#if we have no items at all
		if len(source.rss.channel.find_all('item')) == 0:
			time.sleep(time_to_sleep)
			continue
		#if we have some items, change number of items to upload
		if len(source.rss.channel.find_all('item')) < 50:
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