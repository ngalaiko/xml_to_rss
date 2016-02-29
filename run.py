from bs4 import BeautifulSoup
from bs4 import CData
import telebot
import email.utils
import time
import requests
import os
import glob
import random
import subprocess as sub

phrases = ['Секундочку...', 'Подождите...', 'Один момент...', 'Сейчас все будет...', 'Почти готово...', 'Ждем...','Идет обработка...']

f = open('output.xml', 'r')

#ftp parameters
host = None
ftp_user = None
ftp_password = None
filename = 'upload.xml'
time_to_sleep = None
items_to_upload = None
path_to_folder = None

#form new string to send
ftp_params = 'host: ' + str(host) + '\nuser: ' + str(ftp_user) + '\npassword: ' + str(ftp_password) + '\nИмя файла на ftp сервере: ' + str(filename) + '\nПериод загрузки: ' + str(time_to_sleep) + ' c\nКоличество товаров в файле: ' + str(items_to_upload) + '\nПуть к папке на сервере для загрузки: ' + str(path_to_folder)

#if we are ready to start new convertation
ready = True
#path to xml files
path = './files/*'

#upload.py process
proc = None

def convert(finput):
	#opening files
	xml = BeautifulSoup(open(finput, 'r').read(), features = 'xml')
	rss = BeautifulSoup(open('output.xml', 'r').read(), features = 'xml')
	#listing xml categories and remembering them
	categories = {}
	for category in xml.yml_catalog.categories.find_all('category'):
		categories[category['id']] = category.string
	#listing xml offers, converting them to rss items and appending to result
	for offer in xml.yml_catalog.offers.find_all('offer')[::-1]:
		#creating new item
		#insert after <atom:link>
		rss.rss.channel.find_all('link', limit = 3)[2].insert_after(BeautifulSoup.new_tag(name = 'item', self = rss))
		rss.rss.channel.item.append(BeautifulSoup.new_tag(self = rss, name = "title"))
		rss.rss.channel.item.title.string = offer.find_all('name')[0].string.replace('&quot;', '\"')
		rss.rss.channel.item.append(BeautifulSoup.new_tag(self = rss, name = "guid"))
		rss.rss.channel.item.guid.string = offer.url.string
		rss.rss.channel.item.append(BeautifulSoup.new_tag(self = rss, name = "link"))
		rss.rss.channel.item.link.string = offer.url.string
		rss.rss.channel.item.append(BeautifulSoup.new_tag(self = rss, name = "description"))
		#check if no description or no picture
		description_string = ''
		picture_string = ''
		if offer.picture:
			picture_string = offer.picture.string
		else:
			picture_string = 'https://upload.wikimedia.org/wikipedia/commons/9/9a/%D0%9D%D0%B5%D1%82_%D1%84%D0%BE%D1%82%D0%BE.png'
		if offer.description:
			description_string = offer.description.string[:offer.description.string.find('//')]
		else:
			description_string = 'Нет описания'
		rss.rss.channel.item.description.string = CData(description_string + '<br/><a href=\'' + offer.url.string + '\'>Купить тут &rarr;</a></br><a href=\'' + offer.url.string + '\'><img src=\'' + picture_string + '\'/></a>')
		rss.rss.channel.item.append(BeautifulSoup.new_tag(self = rss, name = "pubDate"))
		rss.rss.channel.item.pubDate.string = email.utils.formatdate(time.mktime(time.gmtime(int(offer.modified_time.string))))
		rss.rss.channel.item.append(BeautifulSoup.new_tag(self = rss, name = "category"))
		rss.rss.channel.item.category.string = categories[offer.categoryId.string]
	#write to file
	output = open('output.xml', 'w')
	output.write(rss.prettify())
	output.close()

	return output

def download_file(url):
    local_filename = './files/' + url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename

def clear_folder():
	files = glob.glob(path)
	for f in files:
	    os.remove(f)

def count_files():
	files = glob.glob(path)
	count = 0
	for f in files:
		count += 1
	return count

help_message = '/download - скачать сконвертированный файл\n/count - посчитать, сколько товаров в очереди на добавление'

#authorization in telegram
TOKEN = '150331515:AAE-Dbe8DucztItsg5Eh6o1U_g-ZDjnOhck'
bot = telebot.TeleBot(TOKEN, True)

@bot.message_handler(commands = ['start'])
def send_start(message):
	bot.send_message(message.chat.id, 'Присылаешь мне XML файлы, я гружу их на сервер в виде RSS. Список команд смотри, введя \'/\'\n\n (c) @galayko')

@bot.message_handler(commands = ['help'])
def send_help(message):
	bot.send_message(message.chat.id, 'Сначала пришлите мне все XML файлы, которые требуется конвертировать в RSS.\nЗатем, вызовите команду /convert для начала конвертации.\n' + help_message)

@bot.message_handler(commands = ['set_host'])
def set_host(message):
	global host

	#check for empty param
	if message.text.find(' ') < 0:
		bot.send_message(message.chat.id, 'Пустой аргумент')
		return		

	host = message.text[message.text.find(' ') + 1: ]

	#form new string to send
	ftp_params = 'host: ' + str(host) + '\nuser: ' + str(ftp_user) + '\npassword: ' + str(ftp_password) + '\nИмя файла на ftp сервере: ' + str(filename) + '\nПериод загрузки: ' + str(time_to_sleep) + ' c\nКоличество товаров в файле: ' + str(items_to_upload) + '\nПуть к папке на сервере для загрузки: ' + str(path_to_folder)

	bot.send_message(message.chat.id, 'Установлено:\n' + ftp_params)

@bot.message_handler(commands = ['set_user'])
def set_user(message):
	global ftp_user

	#check for empty param
	if message.text.find(' ') < 0:
		bot.send_message(message.chat.id, 'Пустой аргумент')
		return

	ftp_user = message.text[message.text.find(' ') + 1: ]

	#form new string to send
	ftp_params = 'host: ' + str(host) + '\nuser: ' + str(ftp_user) + '\npassword: ' + str(ftp_password) + '\nИмя файла на ftp сервере: ' + str(filename) + '\nПериод загрузки: ' + str(time_to_sleep) + ' c\nКоличество товаров в файле: ' + str(items_to_upload) + '\nПуть к папке на сервере для загрузки: ' + str(path_to_folder)

	bot.send_message(message.chat.id, 'Установлено:\n' + ftp_params)

@bot.message_handler(commands = ['set_password'])
def set_password(message):
	global ftp_password

	#check for empty param
	if message.text.find(' ') < 0:
		bot.send_message(message.chat.id, 'Пустой аргумент')
		return

	ftp_password = message.text[message.text.find(' ') + 1: ]

	#form new string to send
	ftp_params = 'host: ' + str(host) + '\nuser: ' + str(ftp_user) + '\npassword: ' + str(ftp_password) + '\nИмя файла на ftp сервере: ' + str(filename) + '\nПериод загрузки: ' + str(time_to_sleep) + ' c\nКоличество товаров в файле: ' + str(items_to_upload) + '\nПуть к папке на сервере для загрузки: ' + str(path_to_folder)

	bot.send_message(message.chat.id, 'Установлено:\n' + ftp_params)

@bot.message_handler(commands = ['set_filename'])
def set_filename(message):
	global filename

	#check for empty param
	if message.text.find(' ') < 0:
		bot.send_message(message.chat.id, 'Пустой аргумент')
		return

	buff = message.text[message.text.find(' ') + 1: ]
	if buff.split('.')[-1] == 'xml' and buff.split('.')[0] != '':
		filename = buff

		#form new string to send
		ftp_params = 'host: ' + str(host) + '\nuser: ' + str(ftp_user) + '\npassword: ' + str(ftp_password) + '\nИмя файла на ftp сервере: ' + str(filename) + '\nПериод загрузки: ' + str(time_to_sleep) + ' c\nКоличество товаров в файле: ' + str(items_to_upload) + '\nПуть к папке на сервере для загрузки: ' + str(path_to_folder)

		bot.send_message(message.chat.id, 'Установлено:\n' + ftp_params)
	else:
		bot.send_message(message.chat.id, 'Формат файла должен быть .xml')

@bot.message_handler(commands = ['set_time'])
def set_time(message):
	global time_to_sleep

	#check for empty param
	if message.text.find(' ') < 0:
		bot.send_message(message.chat.id, 'Пустой аргумент')
		return

	buff = message.text[message.text.find(' ') + 1: ]
	try:
		int(buff)
	except:
		bot.send_message(message.chat.id, 'Введите целое число')
		return
	time_to_sleep = buff

	#form new string to send
	ftp_params = 'host: ' + str(host) + '\nuser: ' + str(ftp_user) + '\npassword: ' + str(ftp_password) + '\nИмя файла на ftp сервере: ' + str(filename) + '\nПериод загрузки: ' + str(time_to_sleep) + ' c\nКоличество товаров в файле: ' + str(items_to_upload) + '\nПуть к папке на сервере для загрузки: ' + str(path_to_folder)

	bot.send_message(message.chat.id, 'Установлено:\n' + ftp_params)

@bot.message_handler(commands = ['set_items'])
def set_items(message):
	global items_to_upload

	#check for empty param
	if message.text.find(' ') < 0:
		bot.send_message(message.chat.id, 'Пустой аргумент')
		return

	buff = message.text[message.text.find(' ') + 1: ]
	try:
		int(buff)
	except:
		bot.send_message(message.chat.id, 'Введите целое число')
		return
	items_to_upload = buff

	#form new string to send
	ftp_params = 'host: ' + str(host) + '\nuser: ' + str(ftp_user) + '\npassword: ' + str(ftp_password) + '\nИмя файла на ftp сервере: ' + str(filename) + '\nПериод загрузки: ' + str(time_to_sleep) + ' c\nКоличество товаров в файле: ' + str(items_to_upload) + '\nПуть к папке на сервере для загрузки: ' + str(path_to_folder)

	bot.send_message(message.chat.id, 'Установлено:\n' + ftp_params)

@bot.message_handler(commands = ['set_path'])
def set_path(message):
	global path_to_folder

	#check for empty param
	if message.text.find(' ') < 0:
		bot.send_message(message.chat.id, 'Пустой аргумент')
		return

	buff = message.text[message.text.find(' ') + 1: ]
	if buff[0] == '/':
		path_to_folder = buff

		#form new string to send
		ftp_params = 'host: ' + str(host) + '\nuser: ' + str(ftp_user) + '\npassword: ' + str(ftp_password) + '\nИмя файла на ftp сервере: ' + str(filename) + '\nПериод загрузки: ' + str(time_to_sleep) + ' c\nКоличество товаров в файле: ' + str(items_to_upload) + '\nПуть к папке на сервере для загрузки: ' + str(path_to_folder)

		bot.send_message(message.chat.id, 'Установлено:\n' + ftp_params)
	else:
		bot.send_message(message.chat.id, 'Путь вида /path/to/folder')

@bot.message_handler(commands = ['start_uploading'])
def start_uploading(message):
	global proc 

	if not check_upload():
		proc = sub.Popen(['python', 'upload.py', '-ftp_host', 'galayko.ru', '-user', 'galayko', '-password', '123', '-time', '2323', '-items', '2324', '-path', '~/', '-filename', 'upload.xml'])
		bot.send_message(message.chat.id, 'Загрузка началась')
	else:
		bot.send_message(message.chat.id, 'Загрузка уже идет')

def check_upload():
	try:
		if proc.poll():
			return False
		else:
			return True
	except:
		if not proc:
			return False
		return True

def stop_upload(chat_id):
	global proc

	if check_upload():
		os.kill(proc.pid, sub.signal.SIGKILL)
		proc = None
		bot.send_message(chat_id, 'Загрузка остановлена')
	else:
		bot.send_message(chat_id, 'Загрузка неактивна')

@bot.message_handler(commands = ['stop_uploading'])
def stop_uploading(message):
	stop_upload(message.chat.id)

@bot.message_handler(commands = ['get_params'])
def get_params(message):
	#form new string to send
	ftp_params = 'host: ' + str(host) + '\nuser: ' + str(ftp_user) + '\npassword: ' + str(ftp_password) + '\nИмя файла на ftp сервере: ' + str(filename) + '\nПериод загрузки: ' + str(time_to_sleep) + ' c\nКоличество товаров в файле: ' + str(items_to_upload) + '\nПуть к папке на сервере для загрузки: ' + str(path_to_folder)

	bot.send_message(message.chat.id, 'Установлено:\n' + ftp_params)

@bot.message_handler(content_types = ['document'])
def add_file(message):
	stop_upload(message.chat.id)

	file_info = bot.get_file(message.document.file_id)
	download_file('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))
	bot.send_message(message.chat.id, 'Файл загружен.\nЗагрузите еще файл или начните обработку командой /convert')

@bot.message_handler(commands = ['download'])
def send_file(message):
	stop_upload()

	bot.send_message(message.chat.id, random.choice(phrases)) 
	#send file
	doc = open('output.xml', 'rb')
	bot.send_document(message.chat.id, doc)

@bot.message_handler(commands = ['clear'])
def send_file(message):
	stop_upload()

	bot.send_message(message.chat.id, random.choice(phrases)) 
	#clean output.xml
	f1 = open('output.xml', 'w')
	f2 = open('start.xml', 'r')
	f1.write(f2.read())
	f1.close()
	f2.close()
	bot.send_message(message.chat.id, 'Файл очищен, очередь пуста.') 

@bot.message_handler(commands = ['count'])
def count_items(message):
	bot.send_message(message.chat.id, random.choice(phrases)) 
	#counting
	rss = BeautifulSoup(open('output.xml', 'r').read(), features = 'xml')
	count = len(rss.rss.channel.find_all('item'))
	bot.send_message(message.chat.id, 'В очереди: ' + str(count)) 

@bot.message_handler(commands = ['convert'])
def convert_files(message):
	global ready

	if count_files() == 0:
		bot.send_message(message.chat.id, 'Сначала добавьте файлы, для этого просто отправьте их мне.')
		return
	if ready:
		try:
			ready = False
			bot.send_message(message.chat.id, 'Обработка началась...')
			#convert all files
			files = glob.glob(path)
			for f in files:
			    convert(f)
			#counting
			rss = BeautifulSoup(open('output.xml', 'r').read(), features = 'xml')
			count = len(rss.rss.channel.find_all('item'))
			bot.send_message(message.chat.id, 'Файл дополнен.\nВ очереди: ' + str(count) + '\n' + help_message)
			#removing files from folder
			clear_folder()
			ready = True
		except:
			bot.send_message(message.chat.id, 'Не удалась конвертация, убедитесь в том, что вы загружаете файлы в XML формате. \nЕсли вы в этом уверены, перешлите файл @galayko, будем разбираться.')
			#removing files from folder
			clear_folder()
	else:
		bot.send_message(message.chat.id, random.choice(phrases))

bot.polling()