#WEBAUTO PROJECT -- COPYRIGHT 2020.08.27
#Author: Rico Paul
#All right Reserved!!!

import asyncio
import threading
import requests
import json
import os
import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select,WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#LOGGING SETUP

log = logging.basicConfig(filename= "Log.txt",
                          filemode= "a",
                          format= "%(asctime)s - Line: %(lineno)d - %(message)s",
                          level= logging.DEBUG)

#THREAD INIT

class Thread:
    def __init__(self,target,*args):
        self.target = target
        self.args = args
        self.thread = threading.Thread(target=self.target,args=self.args)

    def start(self):
        self.thread.start()

    def join(self):
        self.thread.join()

#ENGINE INIT

class SearchEngine:
    def __init__(self,
                 car : str,
                 type = "",
                 other = "",
                 fyear=0,tyear=0,
                 gas=True,
                 dis=True,
                 lpg=True,
                 elec=True,
                 hyb=True):

        #Data ----------------------
        self.car = car
        self.type = type
        self.other = other
        self.fyear = fyear
        self.tyear = tyear
        self.gas = gas
        self.dis = dis
        self.lpg = lpg
        self.hyb = hyb
        self.elec = elec

    def __DriverInit(self):

        #Thread control

        lock = threading.Lock()
        lock.acquire()

        #Options

        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--log-level=3")
        opts.add_argument("--window-size=1920,1080")

        #Driver Init

        self.driver = webdriver.Firefox()  # Driver
        self.header = {"user-agent":
                           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/80.0.3987.132 Safari/537.36"}

        lock.release()
        return self.driver


    def Hasznalt(self):

        #Selenium Driver Init.

        driver = self.__DriverInit()
        driver.get("https://www.hasznaltauto.hu/")

        #Popup

        wait = WebDriverWait(driver,10)
        element = wait.until(EC.presence_of_element_located((By.ID, "CybotCookiebotDialog")))
        element = driver.find_element_by_id("CybotCookiebotDialog")
        driver.execute_script("arguments[0].style.visibility='hidden'", element)

        #Detailed Search
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "toggleAbButton")))
        element = driver.find_element_by_class_name("toggleAbButton")
        element.click()

        #Car

        titlebox = driver.find_element_by_id("hirdetesszemelyautosearch-marka_id")
        titlebox_options = titlebox.find_elements_by_tag_name("option")
        found = False

        for option in titlebox_options:
            if self.car in option.text or self.car.upper() in option.text:
                titlebox_select = Select(titlebox).select_by_value(option.get_attribute("value"))
                found = True
                break

        if not found:
            print("HASZNALT: Car not found")
            logging.error("HASZNALT: Car not found")
            return

        #Model

        if self.type:
            modelbox = driver.find_element_by_id("hirdetesszemelyautosearch-modell_id")
            modelbox_options = modelbox.find_elements_by_tag_name("option")
            found = False

            for option in modelbox_options:
                if self.type in option.text or self.type.upper() in option.text.upper():
                    modelbox_select = Select(modelbox).select_by_value(option.get_attribute("value"))
                    found = True
                    break

            if not found:
                logging.error("HASZNALT: Model not found!")
                print("HASZNALT: Model not found!")
                return

        #Other

        if self.other:
            otherbox = driver.find_element_by_id("hirdetesszemelyautosearch-tipusjel")
            otherbox.send_keys(self.other)

        #From Year

        if self.fyear != 0:
            fyearbox = driver.find_element_by_id("hirdetesszemelyautosearch-evjarat_min")
            fyearbox_select = Select(fyearbox).select_by_value(str(self.fyear))

        #To Year

        if self.tyear != 0:
            tyearbox = driver.find_element_by_id("hirdetesszemelyautosearch-evjarat_max")
            tyearbox_select = Select(tyearbox).select_by_value(str(self.tyear))

        #Fuel types

        btns = driver.find_elements_by_tag_name("button")
        btns[7].click()
        fuel = driver.find_element_by_xpath("//ul[contains(@class,'multiselect-container') and "
                                                 "contains(@class,'dropdown-menu')]")

        fuels = fuel.find_elements_by_class_name("multiselect-item")

        if self.gas:
            fuels[0].click()
        if self.dis:
            fuels[1].click()
        if self.lpg:
            fuels[2].click()
        if self.elec:
            fuels[4].click()
        if self.hyb:
            fuels[3].click()

        #Results
        selectbox = driver.find_element_by_id("hirdetesszemelyautosearch-results")
        selectbox.click()
        select = Select(selectbox)
        select.select_by_value("100")

        #Search

        search_button = driver.find_element_by_name("submitKereses")
        search_button.click()

        #Wait for other site

        WebDriverWait(driver,5).until(EC.presence_of_element_located((By.ID, "talalati")))

        #Give Url for BS4

        url = driver.current_url
        driver.close()

        #------------------------------------------------

        #BeautifulSoup

        site = requests.get(url, headers=self.header).text
        soup = BeautifulSoup(site,"lxml")

        #Find Page Number

        try:
            page_div = soup.find("div", {"class":["text-center","link-pager-container"]})
            pagebox = page_div.find("ul", class_="pagination")
            lastpage = pagebox.find("li", class_="last").find("a").text
        except:
            lastpage = 1 #If Pagination not found, set page to 1

        #Find Content box

        contentbox = soup.find("div",{"id":"talalati"})
        contentbox_child = contentbox.find_all(class_="list-view")
        if len(contentbox_child) > 1:
            contentbox_child = contentbox_child[1]
        else:
            contentbox_child = contentbox_child[0]
        contents = contentbox_child.find_all("div", {"class":["row talalati-sor","swipe-watch"],"data-swipe-direction":"left"})

        #Create folder for this site

        if not os.path.exists("Sites/Hasznalt"):
            os.mkdir("Sites/Hasznalt")

        #Parse through all the cars

        time.sleep(0.2) # Wait pictures to load

        j = 0 # Folder counter

        for c in contents:
            j+=1
            data = {}

            try:
                os.mkdir(f"Sites/Hasznalt/{j}")
            except FileExistsError:
                pass

            #Save Thumbnail

            thumbnail = c.find("img",class_="img-responsive")["src"]

            with open(f"Sites/Hasznalt/{j}/thumb.jpg","wb") as f:
                f.write(requests.get(thumbnail).content)

            #Search infos

            title = c.find("h3").find("a")
            price = c.find("div", class_="vetelar")

            data["title"] = title.text
            data["link"] = title.get("href")
            data["price"] = price.text

            infobox = c.find("div",{"class":["talatisor-info","adatok"]})
            infobox_infos = infobox.find_all("span",class_="info")

            infos = ["fuel","age","encap","tq","hp","km"]

            #Save infos

            for info,i in zip(infobox_infos,infos):
                try:
                    data[i] = info.text
                    if "encap" in i:
                        aux = data[i]
                        data[i] = aux[:len(aux)-4]
                except:
                    data[i] = "Unknown"

            #Dump JSON file

            with open(f"Sites/Hasznalt/{j}/data.json","w",encoding="iso8859_2") as f:
                json.dump(data,f,indent=4,ensure_ascii=False)

        #Next Page

        if int(lastpage) > 1:

            for p in range(2,int(lastpage)+1):

                #Init

                site = requests.get(url + f"/page{p}", headers=self.header).text
                soup = BeautifulSoup(site, "lxml")

                #Contentbox

                contentbox = soup.find(id="talalati")
                contentbox_child = contentbox.find(id="w26")
                contents = contentbox_child.find_all("div", {"class": ["row talalati-sor", "swipe-watch"],
                                                             "data-swipe-direction": "left"})

                #Loop Through Contentbox

                for c in contents:
                    j+=1
                    data = {}

                    try:
                        os.mkdir(f"Sites/Hasznalt/{j}")
                    except FileExistsError:
                        pass

                    # Save Thumbnail

                    thumbnail = c.find("img", class_="img-responsive").get("src")

                    with open(f"Sites/Hasznalt/{j}/thumb.jpeg","wb") as f:
                        f.write(requests.get(thumbnail).content)

                    # Search Infos

                    title = c.find("h3").find("a")
                    price = c.find("div",class_="vetelar")

                    data["title"] = title.text
                    data["link"] = title.get("href")
                    data["price"] = price.text

                    infobox = c.find("div", {"class": ["talatisor-info", "adatok"]})
                    infobox_infos = infobox.find_all("span", class_="info")

                    infos = ["fuel", "age", "encap", "tq", "hp", "km"]

                    #Save infos

                    for info,i in zip(infobox_infos,infos):
                        try:
                            data[i] = info.text
                            if "encap" in i:
                                aux = data[i]
                                data[i] = aux[:len(aux) - 4]
                        except:
                            data[i] = "Unknown"

                    #Dump JSON file

                    with open(f"Sites/Hasznalt/{j}/data.json", "w", encoding="iso8859_2") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

        return


    def Olx(self):

        #SeleniumDriver init.

        driver = self.__DriverInit()
        driver.get("https://www.olx.ro/auto-masini-moto-ambarcatiuni/autoturisme/")

        # Popup

        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.ID, "onetrust-consent-sdk")))
        element = driver.find_element_by_id("onetrust-consent-sdk")
        driver.execute_script("arguments[0].style.display='none'", element)

        time.sleep(0.2)

        #Find Car

        cardropdown = driver.find_element_by_xpath("//span[contains(@class, '3rd-category-choose-label')"
                                                          "and contains(@class, 'header')"
                                                          "and contains(@class, 'block')]")
        cardropdown.click()
        cardropdown_content = driver.find_element_by_xpath("//ul[contains(@class, 'small') "
                                                           "and contains(@class, suggestinput) "
                                                           "and contains(@class, bgfff)"
                                                           "and contains(@class, lheight20)"
                                                           "and contains(@class, br-3)"
                                                           "and contains(@class, abs)"
                                                           "and contains(@class, subcategories)"
                                                           "and contains(@class, binded)]")

        cardropdown_content_select = driver.find_elements_by_tag_name("li")
        for car in cardropdown_content_select:
            a = car.find_element_by_tag_name("a")
            carname = a.get_attribute("data-code")

            if carname is None:
                continue

            if self.car.lower() in carname:
                car.click()
                break

        time.sleep(0.2)

        #Find Type

        if self.type != "":

            typecontainer = driver.find_element_by_xpath("//div[contains(@class, 'filter-item')"
                                                        "and contains(@class, 'rel')"
                                                        "and contains(@class, 'filter-item-model')]")

            typebox = typecontainer.find_element_by_tag_name("a")
            action = ActionChains(driver)
            action.move_to_element(typebox)
            action.click()
            action.perform()

            typedropdown_content = typecontainer.find_element_by_xpath("//ul[contains(@class, 'small') "
                                                                "and contains(@class, 'suggestinput') "
                                                                "and contains(@class, 'bgfff')"
                                                                "and contains(@class, 'lheight20')"
                                                                "and contains(@class, 'br-3')"
                                                                "and contains(@class, 'abs')"
                                                                "and contains(@class, 'select')"
                                                                "and contains(@class, 'binded')]")

            types = typedropdown_content.find_elements_by_xpath("//li[contains(@class, 'dynamic')"
                                                                "and contains(@class, 'clr')"
                                                                "and contains(@class, 'brbott-4')]")

            for t in types:
                cartype_pillar = t.find_elements_by_tag_name("label")
                cartype = cartype_pillar[1]

                if cartype is None:
                    continue

                if self.type.lower() in str(cartype.get_attribute("data-value")).lower():
                    t.click()
                    break

        time.sleep(0.2)

        #Fyear

        fyearbox = driver.find_elements_by_xpath("//div[contains(@class, 'filter-item') "
                                                      "and contains(@class, 'filter-item-from') "
                                                      "and contains(@class, 'rel')"
                                                      "and contains(@class, 'numeric-item')]")

        fyearbutton = fyearbox[1].find_element_by_tag_name("a")

        fyearbutton.click()
        yearinput = fyearbox[1].find_element_by_tag_name("input")

        yearinput.send_keys(self.fyear)

        time.sleep(0.2)

        #Lyear

        lyearbox = driver.find_elements_by_xpath("//div[contains(@class, 'filter-item') "
                                                 "and contains(@class, 'filter-item-to') "
                                                 "and contains(@class, 'rel')"
                                                 "and contains(@class, 'numeric-item')]")

        lyearbutton = lyearbox[1].find_element_by_tag_name("a")

        lyearbutton.click()
        yearinput = lyearbox[1].find_element_by_tag_name("input")

        yearinput.send_keys(self.tyear)

        time.sleep(0.2)

        #Fuel Types   #BUGFIX

        if not all([self.gas, self.dis, self.lpg, self.hyb, self.elec]):
            fuelbox = driver.find_element_by_xpath("//div[contains(@class, 'filter-item')"
                                                   "and contains(@class, 'rel')"
                                                   "and contains(@class, 'filter-item-petrol')]")

            fuelcheck = fuelbox.find_element_by_tag_name("a")

            action = ActionChains(driver)
            action.move_to_element_with_offset(fuelcheck, 0, 5)
            action.click()
            action.perform()

            fueldropdown_content = typecontainer.find_elements_by_xpath("//ul[contains(@class, 'small') "
                                                                        "and contains(@class, 'suggestinput') "
                                                                        "and contains(@class, 'bgfff')"
                                                                        "and contains(@class, 'lheight20')"
                                                                        "and contains(@class, 'br-3')"
                                                                        "and contains(@class, 'abs')"
                                                                        "and contains(@class, 'select')"
                                                                        "and contains(@class, 'binded')]")

            fuels = fueldropdown_content[1].find_elements_by_xpath("//li[contains(@class, 'dynamic') "
                                                                   "and contains(@class, 'clr') "
                                                                   "and contains(@class, 'brbott-4')] ")

            if self.gas:
                check = 0
            elif self.dis:
                check = 1
            elif self.lpg:
                check = 2
            elif self.hyb:
                check = 3
            elif self.elec:
                check = 4

            action = ActionChains(driver)
            action.move_to_element(fuels[check])
            action.click()
            action.perform()

        #Close Selenium

        url = driver.current_url
        driver.close()

        #-----------------------------------

        #Create Folder

        if not os.path.exists("Sites/Olx"):
            os.mkdir("Sites/Olx")

        #BS4

        site = requests.get(url,headers=self.header).text
        soup = BeautifulSoup(site,"lxml")

        results = soup.find_all("tr",class_="wrap")

        j = 0

        for result in results:
            data = {}
            j += 1 #Folder Counter
            if not os.path.exists(f"Sites/Olx/{j}"):
                os.mkdir(f"Sites/Olx/{j}")

            #Get Thumbnail

            thumbbox = result.find("td",class_="photo-cell")
            thumb = thumbbox.find("img")["src"]
            with open(f"Sites/Olx/{j}/thumb.jpg","wb") as f:
                f.write(requests.get(thumb).content)

            #Get Data

            databox = result.find("td",class_="title-cell")
            data["title"] = databox.find("strong").text
            data["link"] = databox.find("a")["href"]
            data["price"] = result.find("p",class_="price").find("strong").text
            data["fuel"] = "unknown"
            data["age"] = "unknown"
            data["encap"] = "unknown"
            data["tq"] = "unknown"
            data["hp"] = "unknown"
            data["km"] = "unknown"

            with open(f"Sites/Olx/{j}/data.json","w", encoding="utf8") as f:
                json.dump(data,f, indent=4, ensure_ascii=False)

        return

    def AutoScout(self):
        #Driver Init

        driver = self.__DriverInit()
        driver.get("https://www.autoscout24.com/refinesearch")

        #Popup
        wait = WebDriverWait(driver,10)
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@style, 'background: rgba(0, 0, 0, 0.5)')]")))
        element = driver.find_element_by_tag_name("div")
        driver.execute_script("arguments[0].style.display = 'None'", element)

        #Find Base Div

        base = driver.find_element_by_id("details")
        basebox = base.find_element_by_class_name("cl-filters-section-body")
        basebox_divs = basebox.find_elements_by_tag_name("div")
        cardiv = basebox_divs[1]
        cardiv_deep = cardiv.find_element_by_tag_name("div")
        elems = cardiv_deep = cardiv_deep.find_elements_by_xpath("//div[contains(@class,'cl-filter-element')"
                                                                   "and contains(@class,'sc-grid-col-4')"
                                                                   "and contains(@class,'sc-grid-col-m-6')"
                                                                   "and contains(@class,'sc-grid-col-s-12')"
                                                                   "and contains(@class,'cl-filter-wrapper')"
                                                                   "and contains(@class,'cl-mmmv')]")

        #Car

        carbox = elems[0]
        carbox = carbox.find_element_by_tag_name("input")

        #Action to Write in Car

        action = ActionChains(driver)
        action.move_to_element(carbox)
        action.click()
        action.send_keys(self.car)
        action.send_keys(Keys.ENTER)
        action.perform()

        #Type, same as car

        if self.type != "":
            typebox = elems[1]
            typebox = typebox.find_element_by_tag_name("input")

            action = ActionChains(driver)
            action.move_to_element(typebox)
            action.click()
            action.send_keys(self.type)
            action.send_keys(Keys.ENTER)
            action.perform()

        #Other, same as car

        if self.other != "":
            otherbox = elems[2]
            otherbox = otherbox.find_element_by_tag_name("input")

            action = ActionChains(driver)
            action.move_to_element(otherbox)
            action.click()
            action.send_keys(self.other)
            action.send_keys(Keys.ENTER)
            action.perform()

        #Second Layer

        layers = basebox.find_elements_by_class_name("sc-grid-row")
        firstlayer = layers[1]
        secondlayer = layers[5] #Fuelbox IDK how it works but it works

        #Fyear same as Car but derived from layer

        if self.fyear != 0:
            fyearbox = firstlayer.find_element_by_xpath("//span[contains(@data-test,'reg-from')]")
            fyearbox_input = fyearbox.find_element_by_tag_name("input")

            action = ActionChains(driver)
            action.move_to_element(fyearbox_input)
            action.click()
            action.send_keys(self.fyear)
            action.send_keys(Keys.ENTER)
            action.perform()

        #Tyear same as Car but derived from layer

        if self.tyear != 0:
            tyearbox = firstlayer.find_element_by_xpath("//span[contains(@data-test,'reg-to')]")
            tyearbox_input = tyearbox.find_element_by_tag_name("input")

            action = ActionChains(driver)
            action.move_to_element(tyearbox_input)
            action.click()
            action.send_keys(self.tyear)
            action.send_keys(Keys.ENTER)
            action.perform()

        #Fuel Type

        if not all([self.gas,self.dis,self.lpg,self.hyb,self.elec]):
            fuelbox = secondlayer.find_element_by_class_name("as24-custom-dropdown--selected")
            fuelbox.click()

            if self.gas:
                fuel = driver.find_element_by_css_selector('input[id*=fuel-types-B')
                action = ActionChains(driver)
                action.move_to_element(fuel)
                action.click()
                action.perform()
            if self.dis:
                fuel = driver.find_element_by_css_selector('input[id*=fuel-types-D')
                action = ActionChains(driver)
                action.move_to_element(fuel)
                action.click()
                action.perform()
            if self.lpg:
                fuel = driver.find_element_by_css_selector('input[id*=fuel-types-L')
                action = ActionChains(driver)
                action.move_to_element(fuel)
                action.click()
                action.perform()
            if self.hyb:
                fuel = driver.find_element_by_css_selector('input[id*=fuel-types-2')
                action = ActionChains(driver)
                action.move_to_element(fuel)
                action.click()
                action.perform()
            if self.elec:
                fuel = driver.find_element_by_css_selector('input[id*=fuel-types-E')
                action = ActionChains(driver)
                action.move_to_element(fuel)
                action.click()
                action.perform()

        #Submit

        submitbox = driver.find_element_by_xpath("//div[contains(@class,'sc-text-center')"
                                                 "and contains(@class,'sc-sticky')]")

        submitbox.click()

        # Popup
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@style, 'background: rgba(0, 0, 0, 0.5)')]")))
        element = driver.find_element_by_tag_name("div")
        driver.execute_script("arguments[0].style.display = 'None'", element)

        url = driver.current_url+"&size=20"
        driver.close()

        #-----------------------------------------

        #Folder

        if not os.path.exists("Sites/AutoScout"):
            os.mkdir("Sites/AutoScout")

        #BS4
        j = 0 # FolderCount

        for i in range(1,21):
            site = requests.get(url+f"&page={i}", headers=self.header).text
            soup = BeautifulSoup(site, "lxml")

            if "cldt-price" not in site:
                break

            databox = soup.find("div",class_="cl-list-elements")
            carboxes = databox.find_all("div",class_='cl-list-element-gap')

            for i in carboxes:
                data = {}
                j+=1
                if not os.path.exists(f"Sites/AutoScout/{j}"):
                    os.mkdir(f"Sites/AutoScout/{j}")

                #Data

                data["title"] = i.find("div",class_="cldt-summary-titles").text.strip("\n")

                #Thumbnail
                try:
                    with open(f"Sites/AutoScout/{j}/thumb.jpg", "wb") as f:
                        gallerybox = i.find("div", class_="cldt-summary-gallery")
                        imgbox = gallerybox.find("img")["data-src"]
                        f.write(requests.get(imgbox).content)
                except:
                    os.remove(f"Sites/AutoScout/{j}/thumb.jpg")

                data["price"] = i.find("span",class_="cldt-price").text.strip("\n")

                details = i.find("ul",attrs={"data-item-name": "vehicle-details"})
                lis = details.find_all("li")

                data["link"] = f'https://www.autoscout24.com{i.find("a",attrs={"data-item-name": "detail-page-link"})["href"]}'
                data["km"] = lis[0].text.strip("\n")
                data["age"] = lis[1].text.strip("\n")
                data["tq"] = lis[2].text.strip("\n")
                data["hp"] = lis[2].text.strip("\n")
                data["fuel"] = lis[6].text.strip("\n")
                data["encap"] = "Unknown"

                with open(f"Sites/AutoScout/{j}/data.json","w",encoding="utf-8") as f:
                    json.dump(data,f,indent=4,ensure_ascii=False)

        return

    def Autovit(self):
        #Init Driver

        driver = self.__DriverInit()
        driver.get("https://www.autovit.ro/")

        #Popup
        popbox = driver.find_element_by_id("onetrust-accept-btn-handler")
        popbox.click()

        #Car

        carbox = driver.find_element_by_id("filter_enum_make")
        carbox.send_keys(self.car)
        carbox.send_keys(Keys.ENTER)
        time.sleep(0.5)

        #Type

        if self.type:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "filter_enum_model")))

            typebox = driver.find_element_by_id("filter_enum_model")
            typebox.send_keys(self.type)
            typebox.send_keys(Keys.ENTER)
            time.sleep(0.5)

        #Fyear

        if self.fyear:
            fyearbox = driver.find_element_by_id("filter_float_year:from")
            fyearbox.send_keys(self.fyear)
            fyearbox.send_keys(Keys.ENTER)

        #Lyear

        if self.tyear:
            lyearbox = driver.find_element_by_id("filter_float_year:to")
            lyearbox.send_keys(self.tyear)
            lyearbox.send_keys(Keys.ENTER)

        #Fuel

        if not all([self.gas,self.dis,self.elec,self.hyb,self.lpg]):
            fuelbox = driver.find_element_by_id("filter_enum_fuel_type")

            if self.lpg:
                fuelbox.send_keys("Benzina+GPL")
                fuelbox.send_keys(Keys.ENTER)

            elif self.gas:
                fuelbox.send_keys("Benzina")
                fuelbox.send_keys(Keys.ENTER)

            elif self.dis:
                fuelbox.send_keys("Diesel")
                fuelbox.send_keys(Keys.ENTER)

            elif self.hyb:
                fuelbox.send_keys("Hibrid")
                fuelbox.send_keys(Keys.ENTER)

            elif self.elec:
                fuelbox.send_keys("Electric")
                fuelbox.send_keys(Keys.ENTER)

        #Submit


        button = driver.find_element_by_xpath("//button[contains(@class, 'ds-button') and "
                                                       "contains(@class, 'ds-width-full') and "
                                                       "not(contains(@class, 'ds-medium')) and "
                                                       "not(contains(@class, 'ds-neutral'))]")

        button.click()

        #Wait to load

        WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'offers') and "
                                                                                "contains(@class, 'list')]")))
        #Pass url and close driver
        url = driver.current_url
        driver.close()

        #BS4 ------------------------------------------------------

        site = requests.get(url,headers=self.header).text
        soup = BeautifulSoup(site,"lxml")

        #Check Pages

        pagebox = soup.find("ul",class_="om-pager")

        if pagebox:
            nums = pagebox.find_all("li",class_="")
            lastpage = nums[len(nums)-1].a.span.text
        else:
            lastpage = 1

        #Folder Counter
        c = 0

        #Get Car boxes

        for i in range(int(lastpage)):
            maindiv = soup.find("div",attrs={"class":["offers","list"]})
            carboxes = maindiv.find_all("article")

            #Get data

            for j in carboxes:
                #Foldercounter
                c+=1
                #Check Folder exists
                if not os.path.exists(f"Sites/Autovit/{c}"):
                    os.mkdir(f"Sites/Autovit/{c}")

                data = {}
                #Get picture

                pict = j.find("div",class_="offer-item__photo").a.img
                pictdata = pict["data-src"][:-7]
                pictdata += "600x400"

                with open(f"Sites/Autovit/{c}/thumb.jpg","wb") as f:
                    f.write(requests.get(pictdata).content)

                #Data

                data["title"] = j.find("h2").text
                data["link"] = j.find("h2").a["href"]
                data["price"] = j.find("div",class_="offer-price").text

                infobox = j.find("ul",class_="ds-params-block")
                infos = infobox.find_all("li")

                datatype = ["age","km","fuel","encap"]

                for d,inf in zip(datatype,infos):
                    try:
                        data[d] = inf.text
                    except:
                        data[d] = "Unknown"

                data["tq"] = data["hp"] = "Unknown"

                #Dump data

                with open(f"Sites/Autovit/{c}/data.json","w") as f:
                    json.dump(data,f,indent=4,ensure_ascii=False)

        return

    def MobileDe(self):
        #init
        driver = self.__DriverInit()
        driver.get("https://suchen.mobile.de/fahrzeuge/search.html?vc=Car&dam=0&sfmr=false&lang=en")

        #Popup
        wait = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.ID, "gdpr-consent-accept-button")))
        element = driver.find_element_by_id("consentBanner")
        driver.execute_script("arguments[0].style.display='None'",element)

        #Find Car

        carbox = driver.find_element_by_id("selectMake1-ds")
        select = Select(carbox)
        options = select.options
        for i in options:
            if self.car.upper() == i.get_attribute("innerHTML").upper():
                select.select_by_visible_text(i.get_attribute("innerHTML"))
                break

        time.sleep(0.2)

        #Find Make

        modelbox = driver.find_element_by_id("selectModel1-ds")
        select = Select(modelbox)
        options = select.options

        for i in options:
            if self.type.upper() == i.get_attribute("innerHTML").upper():
                select.select_by_visible_text(i.get_attribute("innerHTML"))
                break


        time.sleep(0.2)

        #Find Other

        otherbox = driver.find_element_by_id("modelDescription1-ds")
        otherbox.click()
        otherbox.send_keys(self.other)

        time.sleep(0.2)

        #Find FirstYear

        if self.fyear:
            fyearbox = driver.find_element_by_id("minFirstRegistrationDate")
            fyearbox.send_keys(self.fyear)

        #Find Lastyear

        time.sleep(0.2)

        if self.tyear:
            tyearbox = driver.find_element_by_id("maxFirstRegistrationDate")
            tyearbox.send_keys(self.tyear)

        #Fuel
        #Gas

        time.sleep(0.2)

        if not all([self.gas,self.elec,self.dis,self.lpg,self.hyb]):
            if self.gas:
                fuelbox = driver.find_element_by_id("fuels-PETROL-ds")
                fuelbox.click()
            if self.dis:
                fuelbox = driver.find_element_by_id("fuels-DIESEL-ds")
                fuelbox.click()
            if self.elec:
                fuelbox = driver.find_element_by_id("fuels-ELECTRICITY-ds")
                fuelbox.click()
            if self.hyb:
                fuelbox = driver.find_element_by_id("fuels-HYBRID-ds")
                fuelbox.click()
                fuelbox = driver.find_element_by_id("fuels-HYBRID_DIESEL-ds")
                fuelbox.click()
            if self.lpg:
                fuelbox = driver.find_element_by_id("fuels-LPG-ds")
                fuelbox.click()

        time.sleep(0.3)

        #Search
        button = driver.find_element_by_id("dsp-upper-search-btn")
        button.click()

        #Wait to load
        wait = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.ID, "SRP_SKY_TOP_LEFT")))

        url = driver.current_url
        driver.close()

        #BS4 ------------------------------------------

        site = requests.get(url,headers=self.header).text
        soup = BeautifulSoup(site,"lxml")

        #Folder Counter, and page counter

        c = 0

        if not soup.find("ul",class_="pagination"):
            page=2
        else:
            paginator = soup.find("ul",class_="pagination")
            pages = paginator.find_all("li")
            page = pages[len(pages)-2].text


        #Do it until pages

        for p in range(1,int(page)):

            if p != 1:
                site = requests.get(url + "&pageNumber=" + str(p), headers=self.header).text
                soup = BeautifulSoup(site, "lxml")

            #Get Carboxes seperately

            prebox = soup.find("div", class_="cBox cBox--content cBox--resultList")

            carbox1 = prebox.find_all("div", class_="cBox-body cBox-body--resultitem fsboAd rbt-reg rbt-no-top")

            carbox2 = prebox.find_all("div", class_="cBox-body cBox-body--resultitem dealerAd rbt-reg rbt-no-top")

            #további containerek

            for i in carbox1:
                #Init
                c+=1
                container = i.find("div",class_="g-col-9")
                infocontainer = container.find_all("div",class_="g-row")

                if not os.path.exists(f"Sites/MobileDe/{c}"):
                    os.mkdir(f"Sites/MobileDe/{c}")

                data = {}

                #Get Picture

                picontainer = i.find("div",class_="result-item--image-col")
                picontainer = picontainer.find("div").find("img")
                picurl = picontainer["src"]

                with open(f"Sites/MobileDe/{c}/thumb.jpg","wb") as f:
                    f.write(requests.get("https:"+picurl).content)

                #Get Data

                data["title"] = infocontainer[0].find("span").text
                data["link"] = i.find("a")["href"]
                data["price"] = infocontainer[0].find("div",class_="g-col-4")\
                                                .find("div",class_="price-block u-margin-bottom-9")\
                                                .find("span").text

                #FuelBox

                fueldata = infocontainer[1].find("div",class_="vehicle-data--ad-with-price-rating-label")
                fueldata = fueldata.find_all("div")
                fueldata = fueldata[1].text
                if "Accident-free," in fueldata:
                    fueldata.replace("Accident-free,","")

                fueldata = fueldata.split(",")

                #Databox
                datas = infocontainer[1].find("div").find("div",class_="rbt-regMilPow").text
                datas = datas.split(",")
                data["age"] = datas[0].replace("FR","")
                data["km"] = datas[1]
                data["fuel"] = fueldata[1]
                data["encap"] = "Unknown"
                powerlist = datas[2].split()
                data["tq"] = powerlist[0] + powerlist[1]
                data["hp"] = powerlist[2] + powerlist[3]

                #Dump Data

                with open(f"Sites/MobileDe/{c}/data.json","w") as f:
                    json.dump(data,f,indent=4,ensure_ascii=False)


async def Handler():
    engine = SearchEngine("Mitsubishi","Lancer","Evo",2008,2015) # Inheritance

    #Call The Sites

    #Init Threads

    hasznalt = Thread(engine.Hasznalt)
    olx = Thread(engine.Olx)
    autoscout = Thread(engine.AutoScout)
    autovit = Thread(engine.Autovit)
    mobilede = Thread(engine.MobileDe)

    threads = []
    threads.extend([hasznalt,olx,autoscout,autovit,mobilede])

   #Hasznalt
    try:
        logging.info("Starting Hasznaltauto Scraper")
        print("Starting Hasznalt")
        hasznalt.start()
    except Exception as err:
        logging.error(f"HASZNALTAUTO ERROR! Shutdown Log: {err}")
        print("ERROR: Hasznaltauto")

    #OLX
    try:
        logging.info("Starting OLX Scraper")
        print("Starting OLX")
        olx.start()
    except Exception as err:
        logging.error(f"HASZNALTAUTO ERROR! Shutdown Log: {err}")
        print("ERROR: OLX")

    #AutoScout
    try:
        logging.info("Starting AutoScout Scraper")
        print("Starting Autoscout")
        autoscout.start()
    except Exception as err:
        logging.error(f"AUTOSCOUT ERROR! Shutdown Log: {err}")
        print("ERROR: AutoScout")

    #Autovit

    try:
        logging.info("Starting Autovit Scraper")
        print("Starting Autovit")
        autovit.start()
    except Exception as err:
        logging.error(f"AUTOVIT ERROR! Shutdown Log: {err}")
        print("ERROR: Autovit")

    #Mobile.de

    try:
        logging.info("Starting Mobile.de Scraper")
        print("Starting Mobile.de")
        mobilede.start()
    except Exception as err:
        logging.error(f"MOBILE.DE ERROR! Shutdown Log: {err}")
        print("ERROR: Mobile.de")

    #Collect threads

    for i in threads:
        i.join()
        
if __name__ == "__main__": #Fancy Do Did Done the funny Function :)
    asyncio.run(Handler())