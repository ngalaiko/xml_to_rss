from bs4 import BeautifulSoup
from bs4 import CData
import telebot
import datetime
import requests
import os
import glob

def convert(finput):
	#opening files
	xml = BeautifulSoup(open(finput, 'r').read(), features = 'xml')
	rss = BeautifulSoup(open('output.xml', 'r').read(), features = 'xml')
	#listing xml categories and remembering them
	categories = {}
	for category in xml.yml_catalog.categories.find_all('category'):
		categories[category['id']] = category.string
	#listing xml offers, converting them to rss items and appending to result
	for offer in xml.yml_catalog.offers.find_all('offer'):
		#creating new item
		rss.rss.channel.append(BeautifulSoup.new_tag(name = 'item', self = rss))
		rss.rss.channel.find_all('item')[-1].append(BeautifulSoup.new_tag(self = rss, name = "title"))
		rss.rss.channel.find_all('item')[-1].title.string = offer.find_all('name')[0].string.replace('&quot;', '\"')
		rss.rss.channel.find_all('item')[-1].append(BeautifulSoup.new_tag(self = rss, name = "guid"))
		rss.rss.channel.find_all('item')[-1].guid.string = offer.url.string
		rss.rss.channel.find_all('item')[-1].append(BeautifulSoup.new_tag(self = rss, name = "link"))
		rss.rss.channel.find_all('item')[-1].link.string = offer.url.string
		rss.rss.channel.find_all('item')[-1].append(BeautifulSoup.new_tag(self = rss, name = "description"))
		rss.rss.channel.find_all('item')[-1].description.string = CData(offer.description.string[:200] + '<br/><a href=\'' + offer.url.string + '\'>Читать дальше &rarr;</a></br><a href=\'' + offer.url.string + '\'><img src=\'' + offer.picture.string + '\'/></a>')
		rss.rss.channel.find_all('item')[-1].append(BeautifulSoup.new_tag(self = rss, name = "pubDate"))
		rss.rss.channel.find_all('item')[-1].pubDate.string = '!!!!!!some date' #######
		rss.rss.channel.find_all('item')[-1].append(BeautifulSoup.new_tag(self = rss, name = "author"))
		rss.rss.channel.find_all('item')[-1].author.string = '!!!!!some author' ###########
		rss.rss.channel.find_all('item')[-1].append(BeautifulSoup.new_tag(self = rss, name = "category"))
		rss.rss.channel.find_all('item')[-1].category.string = categories[offer.categoryId.string]
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

#authorization in telegram
TOKEN = '150331515:AAE-Dbe8DucztItsg5Eh6o1U_g-ZDjnOhck'
bot = telebot.TeleBot(TOKEN, True)

@bot.message_handler(commands = ['start'])
def send_start(message):
	bot.send_message(message.chat.id, 'Присылаешь мне XML файлы, я тебе в ответ RSS. Список команд смотри, введя \'/\'\n\n (c) @galayko')

@bot.message_handler(commands = ['help'])
def send_help(message):
	bot.send_message(message.chat.id, 'Сначала пришлите мне все XML файлы, которые требуется конвертировать в RSS.\nЗатем, вызовите команду /convert для начала конвертации.')

@bot.message_handler(content_types=['document'])
def add_file(message):
	file_info = bot.get_file(message.document.file_id)
	download_file('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))
	bot.send_message(message.chat.id, 'Файл загружен.')

@bot.message_handler(commands = ['convert'])
def convert_files(message):
	global ready
	if ready:
		try:
			ready = False
			#clean output.xml
			f1 = open('output.xml', 'w')
			f2 = open('start.xml', 'r')
			f1.write(f2.read())
			f1.close()
			f2.close()
			#convert all files
			files = glob.glob(path)
			for f in files:
			    convert(f)
			#send file
			doc = open('output.xml', 'rb')
			bot.send_document(message.chat.id, doc)
			#removing files from folder
			clear_folder()
			ready = True
		except:
			bot.send_message(message.chat.id, 'Не удалась конвертация, убедитесь в том, что вы загружаете файлы в XML формате.')
			#removing files from folder
			clear_folder()
	else:
		bot.send_message(message.chat.id, 'Идет обработка...')

bot.polling()