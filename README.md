# Scrape Marktplaats
A Simple script to scrape marktplaats, a Dutch Ebay. I scheduled this script nightly, so I got notified on new entries. Which I used when I wanted to buy my first Motorcycle. (Which I found using this script :) )

## Installation
This is a standalone script, you don't need to install it. It does however have some dependencies: `pandas`, `selenium` and `webdriver_manager`, which are easily installed using pip.

Create a virtual python environment

`python3 -m venv .venv`

Activate this environment

`source .venv/bin/activate`

Install necessary dependancies for this script

`pip3 install webdriver_manager pandas selenium`

Furthermore, before you start:
* Get the right geckodriver: every Chrome / Firefox instance needs a different geckodriver

## Run
1. Go to marktplaats, go to the categories you would like to keep track off and get the URl.
2. Modify the `urls` with the respective urls.
3. Run `python scrape_marktplaats.py`

## Counter bot-blocks
Sometimes Marktplaats (or other site you want to scrape) find out you're using a bot and they'll block you. Here we're using two things to counter their blocks.  

### User Agent
First we're changing the user agent of your browser.
The user agent says to the site which browser and OS you're using, but we can change this. 
When getting blocked, we're changing it to another heavy used agent.  

### Proxies
The next thing we're doing is changing the actual url we're accessing the site from. https://www.sslproxies.org/ has a list of proxies, we're simply looping through the list until we've found a proxy which is accepted by Marktplaats.

*Note: that this script and the scraped data are not used commercially.*

