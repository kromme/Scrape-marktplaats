# Scrape Marktplaats
A Simple script to scrape marktplaats, a Dutch Ebay. I scheduled this script nightly, so I got notified on new entries. Which I used when I wanted to buy my first Motorcycle. (Which I found using this script :) )

## Installation
This is a standalone script, you don't need to install it. It does however have two dependencies: `pandas` and `selenium`, which are easily installed using pip.
Furthermore, before you start:
* Get the right geckodriver: every Chrome / Firefox instance needs a different geckodriver
* I'm using Chrome here, change that to your favorite browser

## Run
1. Go to marktplaats, go to the categories you would like to keep track off and get the URl.
2. Modify the `urls` with the respective urls.
3. Run `python scrape_marktplaats.py`

Happy scraping!

Btw, I advice to use a VPN.
