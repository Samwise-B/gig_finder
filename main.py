import requests
import json
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import datetime
import re

def get_page_soup(url, cookies, dynamic):
    # handle cookies in request
    if dynamic == True:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(url)
            # add later if need to load more data
            #load_button = page.get_by_text("Load More")
            #while load_button != None:
            #    load_button.click()
            #    load_button = page.get_by_text("Load More")
            page.wait_for_load_state("networkidle")
#            page.wait_for_url()
            content = page.content()
            browser.close()
    else:
        res = requests.get(url, cookies=cookies)
        content = res.text
    
    
    soup = BeautifulSoup(content, "html.parser")
    return soup

def get_tags(soup, cmds):
    for i in range(0, len(cmds), 2):
        if cmds[i] == "class":
            soup = soup.find_all(class_=cmds[i+1])
        elif cmds[i] == "title":
            soup = soup.find_all(title=cmds[i+1])
        else:
            soup = soup.find_all(cmds[i+1])
    
    return soup

def get_tag(soup, cmds):
    for i in range(0, len(cmds), 2):
        if cmds[i] == "class":
            soup = soup.find(class_=cmds[i+1])
        elif cmds[i] == "title":
            soup = soup.find(title=cmds[i+1])
        else:
            soup = soup.find(cmds[i+1])

    return soup

def get_text_from_tag(tag):
    if tag != None:
        text = tag.get_text().strip()
        text = re.sub("[\n+, \t+]", " ", text)
        text = re.sub("  +", ": ", text)
    else:
        text = None
    return text

def parse_date(date, format):
    if date == None:
        return None
    if format != None:
        pattern = r'(?<=\d)[t, s, r, n][h, t, d, d]'
        date = re.sub(pattern, "", date)
        date = datetime.datetime.strptime(date, format)
        if date.year == 1900:
            date = date.replace(year=datetime.datetime.today().year)
        return date
    else:
        return date

def get_event_links(soup, cmds, baseUrl, relative):
    aTags = get_tags(soup, cmds)

    links = []
    linkDict = {}
    for tag in aTags:
        if relative == True:
            links.append(baseUrl + tag.get('href'))
            linkDict[baseUrl + tag.get('href')] = 0
        else:
            links.append(tag.get('href'))
            linkDict[tag.get('href')] = 0
    
    return list(linkDict.keys())

def getCookiePlaywright(url, cookies):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        page.get_by_text(cookies[2]).click()
        page.wait_for_url(cookies[0])
        cookie_for_requests = (context.cookies()[cookies[1]]['name'], context.cookies()[cookies[1]]['value'])
        print(context.cookies())
        browser.close()
    return cookie_for_requests

def parseCookieTemplate(cookies, cookie_for_request):
    cookieDict = {}
    removeSpaceAndColon = cookies[3].split("; ")
    for var in removeSpaceAndColon:
        split = var.split("=")
        cookieDict[split[0]] = split[1]
    
    cookieDict[cookie_for_request[0]] = cookie_for_request[1]
    print(cookieDict)
    return cookieDict

def parse_html(pageObj, cookies):
    print("getting soup")
    soup = get_page_soup(pageObj['events-url'], cookies, pageObj['dynamic'])

    print("getting event links")
    if pageObj['relative'] == True:
        eventLinks = get_event_links(soup, pageObj['getLinks'], pageObj['base-url'], True)
    else:
        eventLinks = get_event_links(soup, pageObj['getLinks'], pageObj['base-url'], False)

    print("scraping links")
    events = []
    # for each link
    for eventLink in eventLinks:
        # scrape event page
        soup = get_page_soup(eventLink, cookies, pageObj['dynamic'])
        row = []

        # get data
        for (field, data) in pageObj['htmlTags'].items():
            if data != None:
                tag = get_tag(soup, data)
                if field == "link" and tag != None:
                    tag.get('href')
                elif field == "datetime":
                    datetime = parse_date(get_text_from_tag(tag), pageObj['date-format'])
                    if datetime != None and not isinstance(datetime, str):
                        date = datetime.strftime("%m/%d/%Y")
                        time = datetime.strftime("%H:%M:%S")
                        row.append(time)
                        row.append(date)
                    else:
                        row.append(None)
                        row.append(None)
                elif field == "time":
                    time = parse_date(get_text_from_tag(tag), pageObj['time-format'])
                    if time != None and not isinstance(time, str):
                        time = time.strftime("%H:%M")
                    row.append(time)
                elif field == "date":
                    date = parse_date(get_text_from_tag(tag), pageObj['date-format'])
                    if date != None and not isinstance(date, str):
                        date = date.strftime("%m/%d/%Y")
                    row.append(date)
                else:
                    print(f"{field}: {get_text_from_tag(tag)}")
                    row.append(get_text_from_tag(tag))
            else:
                row.append(None)
        
        row.append(eventLink)
        events.append(row)
    
    return events

def convert_string_to_json(elem):
    return json.loads(elem)

def get_dict_element(data, refs):
    elem = data
    for i in range(len(refs)):
        if elem == "":
            return None
        elif refs[i] == "string-to-json":
            elem = convert_string_to_json(elem)
        elif refs[i] == "milliseconds":
            elem = datetime.datetime.fromtimestamp(int(re.sub('\D', '', elem)) / 1000)
        elif isinstance(refs[i], int):
            if len(elem) == 0:
                return None
            elem = elem[refs[i]]
        else:
            elem = elem[refs[i]]

    return elem

def get_dict_elements(data, refs):
    elems = []
    for arr in refs:
        elem = data
        for i in range(len(arr)):
            if elem == "":
                return None
            elif arr[i] == "string-to-json":
                elem = convert_string_to_json(elem)
            elif arr[i] == "milliseconds":
                elem = datetime.datetime.fromtimestamp(re.sub('\D', '', elem) / 1000)
            elif isinstance(arr[i], int):
                if len(elem) == 0:
                    return None
                elem = elem[arr[i]]
            else:
                elem = elem[arr[i]]
        elems.append(elem)

    return elems

def get_api_url(url, api_base, filename):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        # debug: page.on("request", lambda req: print(req.url))
        with page.expect_response("**.json") as res_info:
            page.goto(url)
        api_url = res_info.value.url.split("/")[-2]
        browser.close()
        
    return f"{api_base}{api_url}/{filename}"

def parse_api(page_obj, cookies):
    # if the api url is dynamic get the dynamic url
    if page_obj['dynamic'] == True:
        api_url = get_api_url(page_obj['events-url'], page_obj['api-url'], page_obj['filename'])
    else:
        api_url = page_obj['api-url']


    if page_obj['method'] == "POST":
        res = requests.post(api_url, json=page_obj['body'])
    else:
        res = requests.get(api_url)


    json_data = res.json()
    print("received api json")

    eventList = get_dict_element(json_data, page_obj['event-list'])
    events = []
    for event in eventList:
        row = []
        if page_obj['condition'] == True:
            if get_dict_element(event, page_obj['event-type'][0]) != page_obj['event-type'][1]:
                continue
        for field, data in page_obj['data'].items():
            if data != None:
                if field == "genres":
                    print(f"{field}: {get_dict_elements(event, data)}")
                    row.append(get_dict_elements(event, data))
                elif field == "datetime":
                    datetime = parse_date(get_dict_element(event, data), page_obj['date-format'])
                    if datetime != None and not isinstance(datetime, str):
                        date = datetime.strftime("%m/%d/%Y")
                        time = datetime.strftime("%H:%M:%S")
                        row.append(time)
                        row.append(date)
                    else:
                        row.append(None)
                        row.append(None)
                elif field == "time":
                    time = parse_date(get_dict_element(event, data), page_obj['time-format'])
                    if time != None and not isinstance(time, str):
                        time = time.strftime("%H:%M")
                    row.append(time)
                elif field == "date":
                    date = parse_date(get_dict_element(event, data), page_obj['date-format'])
                    if date != None and not isinstance(date, str):
                        date = date.strftime("%m/%d/%Y")
                    row.append(date)
                elif field == "link":
                    if page_obj['relative'] == True:
                        row.append(page_obj['base-url'] + get_dict_element(event, data))
                    else:
                        row.append(get_dict_element(event, data))
                else:
                    print(f"{field}: {get_dict_element(event, data)}")
                    row.append(get_dict_element(event, data))
            else:
                row.append(None)

        events.append(row)

    return events

def main():
    pageObjects = []
    with open("websites.json", "r") as fp:
        pageObjects = json.load(fp)
    
    events = []
    for pageObj in pageObjects:
        cookies = pageObj['cookies']
        # check for cookie manage
        if pageObj['cookiesRequired'] == True:
            cookie_for_requests = getCookiePlaywright(pageObj['events-url'], pageObj['cookies'])
            cookies = parseCookieTemplate(cookies, cookie_for_requests)
        
        if pageObj['type'] == "html":
            events += parse_html(pageObj, cookies)
        if pageObj['type'] == "api":
            events += parse_api(pageObj, cookies)

    df = pd.DataFrame(events, columns=['title', "time", "date", "price", "genres", "status", "link"])
    
    df.to_excel("events.xlsx", sheet_name="events_table")

    print("Done!")
    return 0
    

if __name__ == '__main__':
    main()