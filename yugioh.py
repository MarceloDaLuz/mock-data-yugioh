import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json
import shutil
import os
import re
from datetime import datetime

def name_of_file(name):
    if name is not None:
        #title = re.sub(r'\s+', '', name)
        title =  re.sub(r'[-()\"#/@;:<>{}`+=~|.!?,]','',name)
        return title

def formated_date(d):
    return d.strftime("%d/%m/%Y %H:%M:%S")

def create_json(path,title,json_content):
    filename =  '{}/{}.json'.format(path,title)
    print("FILENAME : {}".format(filename))
    with open(filename,'w+',encoding='utf8') as f:
        json_string = json.dumps(json_content,ensure_ascii=False)
        f.write(json_string)
    print("DONE! BE HAPPY!")

def deck(url_to_request,deck_folder_uri):
    # READ CARD LIST JSON
    print("http://"+url_to_request)
    URL = "http://"+url_to_request
    try:
        r = requests.get(URL)
        if(r.status_code == 200):
            print("Success!")
            page = BeautifulSoup(r.content,'html5lib')
            ## HEADER
            page_header = page.find('header', attrs = {'id':'broad_title'})
            title_page = page_header.h1.strong.text            

            ## TABLE OF CARDS
            page_content = page.find('div', attrs = {'id' : 'article_body'})
            page_list_cards = page_content.find('ul', attrs = {'class' : 'box_list'})
            deck_card_list = []
            for card in page_list_cards.findAll('li'):
                card_json = {}
                ## CARD INFOS 
                card_info = card.dl

                # CARD NAME 
                card_info_name =  card_info.find('dt', attrs = {'class' : 'box_card_name'})
                card_info_name = card_info_name.find('span', attrs = {'class' : 'card_status'})
                card_json['name'] = card_info_name.strong.text                

                # CARD TYPE 
                card_info_type =  card_info.find('dt', attrs = {'class' : 'box_card_name'})
                card_info_type = card_info_type.find('span', attrs = {'class' : 'card_status'})
                if card_info_type.find('img', alt=True):
                    card_info_type = card_info_type.find('img', alt=True)
                    card_info_type = card_info_type['alt']
                    card_json['type'] = card_info_type
                else:
                    card_json['type'] = 'Normal'        
                
                # CARD SPEC
                card_info_spec = card_info.find('dd', attrs = {'class' : 'box_card_spec'})

                ## CARD SPEC : ATTRIBUTE
                card_info_spec_attr = card_info_spec.find('span', attrs = {'class' : 'box_card_attribute'})            
                card_info_spec_attr = card_info_spec_attr.span.text
                card_json['attribute'] = card_info_spec_attr

                ## CARD SPEC : RANK/LVL
                if card_info_spec.find('span', attrs ={'class' : 'box_card_level_rank'}):
                    card_info_spec_rank = card_info_spec.find('span', attrs ={'class' : 'box_card_level_rank'})
                    card_info_spec_rank = card_info_spec_rank.span.text            
                    card_json['rank'] = card_info_spec_rank

                ## CARD SPEC : SPECIES AND OTHER ITEM
                if card_info_spec.find('span', attrs ={'class' : 'card_info_species_and_other_item'}):
                    card_info_spec_specie_item = card_info_spec.find('span', attrs ={'class' : 'card_info_species_and_other_item'})
                    card_info_spec_specie_item = card_info_spec_specie_item.text  
                    card_info_spec_specie_item = re.sub(r'\s+', '', card_info_spec_specie_item)
                    card_info_spec_specie_item = re.sub(r'^\[', '', card_info_spec_specie_item)
                    card_info_spec_specie_item = re.sub(r'\]$', '', card_info_spec_specie_item)
                    card_info_spec_specie_item = list(card_info_spec_specie_item.split("/")) 
                    card_json['species_and_others'] = card_info_spec_specie_item
                
                ## CARD SPEC : ATK
                if card_info_spec.find('span', attrs = {'class': 'atk_power'}):
                    card_info_spec_atk = card_info_spec.find('span', attrs = {'class' : 'atk_power'})
                    card_info_spec_atk = card_info_spec_atk.text
                    card_info_spec_atk = re.findall("\d+", card_info_spec_atk)                    
                    if card_info_spec_atk is not None and len(card_info_spec_atk) > 0:
                        card_json['atk'] = card_info_spec_atk[0]
                
                ## CARD SPEC : DEF
                if card_info_spec.find('span', attrs = {'class': 'def_power'}):
                    card_info_spec_def = card_info_spec.find('span', attrs = {'class' : 'def_power'})
                    __temp_def = re.sub('DEF','', card_info_spec_def.text)
                    card_info_spec_def = card_info_spec_def.text
                    card_info_spec_def = re.findall("\d+", card_info_spec_def)
                    if card_info_spec_def is not None and len(card_info_spec_def) > 0:
                        card_json['def'] = card_info_spec_def[0]
                    elif 'atk' in card_json:
                        card_json['def'] = __temp_def
                
                # CARD TEXT
                card_info_text = card_info.find('dd', attrs = {'class' : 'box_card_text'})
                if card_info_text is not None:
                    card_json['description'] = str(card_info_text.text)
                
                # CARD LINK                 
                if card.find('input', attrs = {'class': 'link_value'}):
                    card_info_link =  card.find('input', attrs = {'class': 'link_value'}, type = "hidden")
                    data = urlparse(URL)
                    card_info_link = "{}{}".format(data.netloc,card_info_link['value'])                    
                    card_json['link'] = card_info_link
                
                # CARD IMG
                deck_card_list.append(card_json)
            
            ##
            json_structure = {            
                'date' : formated_date(datetime.now()),
                'title' : name_of_file(title_page),
                'card' : deck_card_list
            }
            create_json(deck_folder_uri,'cards',json_structure)     

    except requests.exceptions.ConnectionError:
        r.status_code = "Connection refused"

def create_page_to_spec(content,filename):
    now = datetime.now()
    timestamp = datetime.timestamp(now)    
    f = open("{}{}.html".format(filename,timestamp),"w+")
    f.write(str(content))
    f.close()

def pack(html_page, el, attr_target, attr_value,url):
    # verifica se encontrou a table com os card list
    if html_page.find('{}'.format(el), attrs = {'{}'.format(attr_target):'{}'.format(attr_value)}):
        # anda por todas as tabelas
        page = html_page.find('{}'.format(el), attrs = {'{}'.format(attr_target):'{}'.format(attr_value)})        
        table = page.find('table', attrs = { 'class': 'card_list'})        
        #create(table,"table.html")        
        decks = []
        for tr in table.findAll('tr'):            
            for td in tr.findAll('td'):
                if td.find('div', attrs = {'class' : 'list_body'}):                    
                    for deck_name in td.findAll('div', attrs = {'class':'toggle'}):
                        deck_json = {}
                        deck_json['deck_name'] = str(deck_name.strong.text)
                        deck_json['link'] = '{}{}'.format(url.netloc,deck_name.input['value'])
                        decks.append(deck_json)
        
        json_structure = {            
            'date' : formated_date(datetime.now()),
            'decks' : decks
        }
        create_json('yugioh','card_list',json_structure)

def card_list(url):
    if url is not None:
        try:
            r =  requests.get(url)            
        except requests.exceptions.ConnectionError:
            r.status_code = "Connection refused"
        #
        if r.status_code == 200:
            print("Success!")
            page =  BeautifulSoup(r.content,'html5lib')
            if page is not None:                
                pack(page, 'div', 'id', 'card_list_1',urlparse(url))
            else:
                print("WHITE PAGE!")

def create_deck_folder(name,path):
    # new name
    name = name_of_file(re.sub(r'\s+', '', name))
    path = "{}/{}".format(path,name)   

    if os.path.isdir(path) == False:
        os.mkdir(path)
        return path
    else:
        return path

def read_card_list():
    # check inside yugioh folder
    items = os.listdir('./yugioh')
    # check if json exists inside yugioh folder
    if 'card_list.json' in items:        
        # get json file        
        card_list_file = './yugioh/card_list.json'
        # validate json file
        if os.path.isfile(card_list_file):             
            # read json
             with open(card_list_file, 'r') as f:
                data = json.load(f)
                # check if decks exists in data of file
                if 'decks' in data:
                    #json valido
                    # get all decks on the content of json file
                    total_decks = len(data['decks'])
                    # check if deck folder exists in yugioh folder
                    if 'deck' in items:
                        # deck exists

                        #list decks folder 
                        decks_folder_list = os.listdir('./yugioh/deck')
                        
                        #stupid validate 
                        if len(decks_folder_list) == 0:
                            # empty folder
                            # create deck folders one by one
                            for d in data['decks']:
                                create_deck_folder(d['deck_name'],'./yugioh/deck')    
                        elif len(decks_folder_list) == total_decks:
                            # check inside
                            for deck_folder in decks_folder_list:
                                deck_folder_url = "{}/{}".format('./yugioh/deck',deck_folder)
                                deck_folder_content = os.listdir(deck_folder_url)
                                if len(deck_folder_content) == 0:
                                    #empty deck folder
                                    
                                    # pegar a url do deck
                                    deck_link = ''
                                    for dd in data['decks']:
                                        if deck_folder == name_of_file(re.sub(r'\s+', '', dd['deck_name'])):
                                            deck_link = dd['link']
                                    
                                    # valida o link
                                    if deck_link != '':
                                        deck(deck_link, deck_folder_url)
                                    else:
                                        print("no link for this deck")
                                elif len(deck_folder_content) > 0:
                                   print(":)") 
                        elif len(decks_folder_list) < total_decks:
                            # continue 
                            print("b")
                        elif len(decks_folder_list) > total_decks:
                            # continue too                    
                            print("c")
                    else:
                        #create folder
                        print("d")

                else:
                    card_list("https://www.db.yugioh-card.com/yugiohdb/card_list.action")            
        else:
            card_list("https://www.db.yugioh-card.com/yugiohdb/card_list.action")    
    else:
        card_list("https://www.db.yugioh-card.com/yugiohdb/card_list.action")

def main():    
    read_card_list()

if __name__ == "__main__":
    main()