import requests
from bs4 import BeautifulSoup

website = "https://www.academymusicgroup.com/o2forumkentishtown/events/all"

def getPageSoup(url):
    res = requests.get(url)
    content = res.text
    soup = BeautifulSoup(content, "html.parser")
    return soup

def getEventList(soup):
    mainDiv = soup.find(id="main")
    eventList = mainDiv.find_all("li")
    return eventList

def parseEventList(eventList):
    test = eventList[0]
    textList = []
    textList += test.find_all("span")
    textList += test.find_all("h3")
    textList += test.find_all("a")
    for ele in textList:
        print(ele.get_text())

def main():
    print("getting soup")
    soup = getPageSoup(website)

    print("getting event list")
    eventList = getEventList(soup)

    parseEventList(eventList)
    print("done")

if __name__ == '__main__':
    main()