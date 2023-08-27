import requests
import json
from bs4 import BeautifulSoup

website = "https://www.academymusicgroup.com/o2forumkentishtown/events/all"

def getPageSoup(url):
    res = requests.get(url)
    content = res.text
    soup = BeautifulSoup(content, "html.parser")
    return soup

def getEventLinks(soup, cmds, baseUrl):
    if cmds[0] == "class":
        aTags = soup.find_all(class_=cmds[1])

    links = []
    for tag in aTags:
        links.append(baseUrl + tag.get('href'))
    return links

def main():
    pageObjects = []
    with open("websites2.txt", "r") as fp:
        pageObjects = json.load(fp)
    
    for pageObj in pageObjects:
        print("getting soup")
        soup = getPageSoup(pageObj['events-url'])

        print("getting event links")
        eventLinks = getEventLinks(soup, pageObj['htmlTags']['getLinks'], pageObj['base-url'])

        print("scraping links")
        # for each link
        for eventLink in eventLinks:
            # scrape page
            soup = getPageSoup(eventLink)

            # get artist
            artist = soup
            for i in range(0, len(pageObj['htmlTags']['artist']), 3):
                if pageObj['htmlTags']['artist'][i+1] == "class":
                    artist = artist.find(class_=pageObj['htmlTags']['artist'][i+2])

            if artist != None:
                artist = artist.get_text()
            print("artist:", artist)

            # get date
            date = soup
            for i in range(0, len(pageObj['htmlTags']['date']), 3):
                if pageObj['htmlTags']['date'][i+1] == "class":
                    date = date.find(class_=pageObj['htmlTags']['date'][i+2])
                if pageObj['htmlTags']['date'][i+1] == "tag":
                    date = date.find(pageObj['htmlTags']['date'][i+2])
            if date != None:
                date = date.get_text()
            print("date:", date)

            # get status
            status = soup
            for i in range(0, len(pageObj['htmlTags']['status']),3):
                if pageObj['htmlTags']['status'][i+1] == "class":
                    status = status.find(class_=pageObj['htmlTags']['status'][i+2])
            if status != None:
                status = status.get_text()
            print("status:", status)

    print("Done!")
    return 0
    

if __name__ == '__main__':
    main()