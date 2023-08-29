import requests
import json
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def get_page_soup(url, cookies):
    # handle cookies in request
    if cookies == None:
        res = requests.get(url)
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
    else:
        text = "error: unavailable"
    return text

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
        page.get_by_text("Accept All Cookies").click()
        page.wait_for_url(cookies[1])
        cookie_for_requests = (context.cookies()[1]['name'], context.cookies()[1]['value'])
        print(context.cookies())
        browser.close()
    return cookie_for_requests

def parseCookieTemplate(cookies, cookie_for_request):
    cookieDict = {}
    removeSpaceAndColon = cookies[2].split("; ")
    for var in removeSpaceAndColon:
        split = var.split("=")
        cookieDict[split[0]] = split[1]
    
    cookieDict[cookie_for_request[0]] = cookie_for_request[1]
    print(cookieDict)
    return cookieDict


def main():
    pageObjects = []
    with open("websites.json", "r") as fp:
        pageObjects = json.load(fp)
    
    for pageObj in pageObjects[1:]:
        cookies = pageObj['cookies']
        # check for cookie manage
        if pageObj['cookies'][0] == "True":
            cookie_for_requests = getCookiePlaywright(pageObj['events-url'], pageObj['cookies'])
            cookies = parseCookieTemplate(cookies, cookie_for_requests)
        
        print("getting soup")
        soup = get_page_soup(pageObj['events-url'], cookies)

        print("getting event links")
        if pageObj['relative'] == 'True':
            eventLinks = get_event_links(soup, pageObj['htmlTags']['getLinks'], pageObj['base-url'], True)
        else:
            eventLinks = get_event_links(soup, pageObj['htmlTags']['getLinks'], pageObj['base-url'], False)

        print("scraping links")
        # for each link
        for eventLink in eventLinks:
            # scrape event page
            soup = get_page_soup(eventLink, cookies)

            # get artist
            artist = get_tag(soup, pageObj['htmlTags']['artist'])
            artist = get_text_from_tag(artist)
            print("artist:", artist)

            # get date
            date = get_tag(soup, pageObj['htmlTags']['date'])
            date = get_text_from_tag(date)
            print("date:", date)

            # get status
            status = get_tag(soup, pageObj['htmlTags']['status'])
            status = get_text_from_tag(status)
            print("status:", status)

    print("Done!")
    return 0
    

if __name__ == '__main__':
    main()