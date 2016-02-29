from bs4 import BeautifulSoup
from bs4 import CData
import telebot
import email.utils
import time
import requests
import os
import glob
import random

phrases = ['Секундочку...', 'Подождите...', 'Один момент...', 'Сейчас все будет...', 'Почти готово...', 'Ждем...','Идет обработка...']

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
		rss.rss.channel.item.append(BeautifulSoup.new_tag(self = rss, name = "category"))
		rss.rss.channel.item.find_all('category')[1].string = 'Sale'
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

#if we are ready to start new convertation
ready = True
#path to xml files
path = './files/*'

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

help_message = '/download - скачать сконвертированный файл\n/count - посчитать, сколько товаров в очереди на добавление\n/clear - очистить очередь'

#authorization in telegram
TOKEN = '150331515:AAE-Dbe8DucztItsg5Eh6o1U_g-ZDjnOhck'
bot = telebot.TeleBot(TOKEN, True)

@bot.message_handler(commands = ['start'])
def send_start(message):
	bot.send_message(message.chat.id, 'Присылаешь мне XML файлы, я гружу их на сервер в виде RSS. Список команд смотри, введя \'/\'\n\n (c) @galayko')

@bot.message_handler(commands = ['help'])
def send_help(message):
	bot.send_message(message.chat.id, 'Сначала пришлите мне все XML файлы, которые требуется конвертировать в RSS.\nЗатем, вызовите команду /convert для начала конвертации.\n' + help_message)

@bot.message_handler(content_types = ['document'])
def add_file(message):
	file_info = bot.get_file(message.document.file_id)
	download_file('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))
	bot.send_message(message.chat.id, 'Файл загружен.\nЗагрузите еще файл или начните обработку командой /convert')

@bot.message_handler(commands = ['download'])
def send_file(message):
	bot.send_message(message.chat.id, random.choice(phrases)) 
	#send file
	doc = open('output.xml', 'rb')
	bot.send_document(message.chat.id, doc)

@bot.message_handler(commands = ['clear'])
def send_file(message):
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