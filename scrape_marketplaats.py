# coding: utf-8

import time
import random
import datetime
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By

urls = [
    "https://www.marktplaats.nl/z/motoren/motoren-honda/motor.html?query=motor&categoryId=696&currentPage=1&numberOfResultsPerPage=100&attributes=S%2C10898",
    "https://www.marktplaats.nl/z/motoren/motoren-suzuki/motor.html?query=motor&categoryId=707&currentPage=1&numberOfResultsPerPage=100&attributes=S%2C10898",
    "https://www.marktplaats.nl/z/motoren/motoren-bmw/motor.html?query=motor&categoryId=692&currentPage=1&numberOfResultsPerPage=100&attributes=S%2C10898",
]


class marktplaats_scraper(object):
    """Class for scraping Marktplaats
    """

    def __init__(
        self,
        urls: list,
        output_filename: str = "output.csv",
        use_proxy : bool = True,
    ):
        self.urls = urls
        self.output_filename = output_filename
        self.proxies = pd.DataFrame()
        self.use_proxy = use_proxy

        # define logger
        self._define_logger()

        # set driver profile
        self._set_profile()

        # set driver
        self.DRIVER = self.get_driver()
        if self.use_proxy:
            self.find_proxy()

        # xpaths
        self.XPATH_COOKIE = ".//button[@id='gdpr-consent-banner-accept-button']"
        self.XPATH_POPUP = (
            ".//i[@class='hz-Icon hz-Icon--m hz-SvgIcon hz-SvgIconClose']"
        )
        self.XPATH_BID = ".//span[@class='vip-bid-amount-default-view bid-amount']"
        self.XPATH_BIDDATE = ".//span[@class='vip-bid-date-default-view bid-date']"
        self.XPATH_FIRSTCOLUMN = (
            ".//table[@class='first-column attribute-table single-value-attributes']"
        )
        self.XPATH_SECONDCOLUMN = (
            ".//table[@class='second-column attribute-table single-value-attributes']"
        )
        self.XPATH_PRICE = "//*[@id='listing-root']/div/div[2]/div[1]"
        self.XPATH_TITLE = "//*[@id='listing-root']/div/header/h1"
        self.XPATH_DESCRIPTION = "//*[@id='page-wrapper']/div[4]/section[1]/div[1]/div[5]"
        self.XPATH_SINCE = "//*[@id='listing-root']/div/div[3]/span[3]/span"
        self.XPATH_MPID = "//*[@id='report-root']/div/span"
        self.XPATH_LISTINGS = ".//a[@class='mp-Listing-coverLink']"

        # init
        self.db = []
        self.checked_urls = []

    def _define_logger(self):
        def get_logger(name, logfile="log.log"):
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            logging.basicConfig(
                level=logging.DEBUG, format=log_format, filename=logfile, filemode="w"
            )
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG)
            console.setFormatter(logging.Formatter(log_format))
            logging.getLogger(name).addHandler(console)
            return logging.getLogger(name)

        self.logger = get_logger("marktplaats_scraper")


    def get_driver(self):
        return webdriver.Firefox(firefox_profile = self.profile, 
                                        service=Service(GeckoDriverManager().install()))

    def _change_useragent(self):
        """Change the user agent
        """ 
        
        uas = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        ,'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
        ,'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        ,'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        ,'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8'
        ,'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
        ,'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
        ,'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0']

        ua = random.choice(uas)
        
        self.profile.set_preference("general.useragent.override", ua)
        self.profile.update_preferences() 
        self.logger.info(f'User agent set to {ua}')
        
    def _set_profile(self):
        """Create a profile for FF
        """
        self.profile = webdriver.FirefoxProfile()
        
        # to make sure we can close the windows: https://stackoverflow.com/questions/45510338/selenium-webdriver-3-4-0-geckodriver-0-18-0-firefox-which-combination-w
        self.profile.set_preference("browser.tabs.remote.autostart", False)
        self.profile.set_preference("browser.tabs.remote.autostart.1", False)
        self.profile.set_preference("browser.tabs.remote.autostart.2", False)

        # turn off auto update
        self.profile.set_preference('app.update.auto',False)
        self.profile.set_preference('app.update.enabled',False)
        self.profile.set_preference('app.update.silent',False)
        
        # set user agent
        self._change_useragent()
        
        self.logger.info(f'Profile set')

    def _change_proxy(self, proxyNo : int = 0):
        if len(self.proxies) == 0:
            self._get_proxy_list()
        
        # get next proxy values
        proxy = self.proxies.iloc[proxyNo].host
        port = int(self.proxies.iloc[proxyNo].port)

        # set proxy
        self.profile.set_preference("network.proxy.type", 1)
        self.profile.set_preference("network.proxy.http", proxy)
        self.profile.set_preference("network.proxy.http_port", port)
        self.profile.set_preference("network.proxy.ssl", proxy)
        self.profile.set_preference("network.proxy.ssl_port", port)
        self._change_useragent()
        self.profile.update_preferences() 
        
        self.logger.info(f'Proxy change to {proxy}')
        
    def _get_proxy_list(self):
        """Get list of proxies we can use
        """
        driver = self.get_driver()
        
        # go to page
        driver.get('https://www.sslproxies.org/')
        
        # set to 80 results
        ##driver.find_element_by_xpath("//.[@name='proxylisttable_length']").send_keys('80')
        
        # get table results
        ##table = driver.find_element_by_xpath("//.[@id='proxylisttable']")
        table = driver.find_element_by_xpath("/html/body/section[1]/div/div[2]/div/table")
        rows = table.text.split('\n')[1:80]
        driver.close()
        
        # to dataframe
        hosts = []
        ports = []

        for row in rows:
            try:
                hosts.append(row.split(' ')[0])
                ports.append(row.split(' ')[1])
            except:
                continue
        
        self.proxies = pd.DataFrame({'host': hosts, 'port': ports})
        self.logger.info(f'Got {len(self.proxies)} proxies')


    def find_proxy(self):
        """Trying whether the proxy actually works
        """
        # do not use when no proxy is needed
        if not self.use_proxy:
            return
        success = False
        proxyNo = 0

        while not success:
            self.logger.info(f'Trying proxy number {proxyNo}')
            self._change_proxy(proxyNo = proxyNo)
            
            # start driver
            driver = self.get_driver()
            
            # go to duckduckgo to check ip
            driver.get('https://duckduckgo.com/?q=my+ip&t=hb&ia=answer')
            
            # wait for ip
            wait = WebDriverWait(driver,10)
            wait.until(lambda driver: driver.find_element_by_class_name('zci__body'))
            ip = driver.find_element_by_class_name('zci__body').text
                
            # if that works, check if MP is reachable
            driver.get('https://www.marktplaats.nl')
            
            # check if proxy isnt blocked. other go to except.
            if not ('blocked' in driver.title or 'error' in driver.title.lower()):
                proxyNo += 1
                
                self.DRIVER.close()
                self.DRIVER = self.get_driver()
                self._change_proxy(proxyNo = proxyNo)
                
                if proxyNo >= 79:
                    break
                
            # if works, end loop
            self.logger.info(f'Now working from {ip}')
            success = True
            driver.close()


    def _accept_cookie(self):
        """Accepts cookies
        """
        try:
            self.DRIVER.find_element(By.XPATH, (self.XPATH_COOKIE)).click()
            self.logger.info("Cookie accepted")
        except:
            pass

    def _close_popup(self):
        """Close Popup
        """
        try:
            self.DRIVER.find_element(By.XPATH, (self.XPATH_POPUP)).click()
            self.logger.info("Popup closed")
        except:
            pass

    def scrape_listing(self, url: str):
        """Scrape a single Listing
        """

        # sleep a bit to fool MP
        time.sleep(random.randint(2, 9))

        try:
            # go to url
            self.DRIVER.get(url)

            # get bids
            bids = [
                bid.text for bid in self.DRIVER.find_elements(By.XPATH, (self.XPATH_BID))
            ]
            max_bid = "NA" if len(bids) == 0 else bids[0]

            # get bids dates
            bids_date = [
                date.text
                for date in self.DRIVER.find_elements(By.XPATH, (self.XPATH_BIDDATE))
            ]
            max_bid_date = "NA" if len(bids_date) == 0 else bids_date[0]

            # get info from table
            table = ""
            try:
                table += self.DRIVER.find_element(By.XPATH, (
                    self.XPATH_FIRSTCOLUMN)
                ).text.replace("\n", "|")
            except:
                table += ""

            try:
                table += "|" + self.DRIVER.find_element(By.XPATH, (
                    self.XPATH_SECONDCOLUMN)
                ).text.replace("\n", "|")
            except:
                table += ""

            # gather
            output = {
                "price": self.DRIVER.find_element(By.XPATH, (
                    self.XPATH_PRICE)
                ).text.replace(";", "|"),
                "title": self.DRIVER.find_element(By.XPATH, (
                    self.XPATH_TITLE)
                ).text.replace(";", "|"),
                "description": self.DRIVER.find_element(By.XPATH, (self.XPATH_DESCRIPTION))
                .text.replace("\n", ".")
                .replace(";", "|"),
                "table": table,
                "max_bid": max_bid,
                "max_bid_date": max_bid_date,
                "listing_url": self.DRIVER.current_url,
                "bids": bids,
                "bids_date": bids_date,
                "since": self.DRIVER.find_element(By.XPATH, (self.XPATH_SINCE)).text,
                "MP_ID": self.DRIVER.find_element(By.XPATH, (self.XPATH_MPID)).text,
            }
            return output

        except Exception as e:
            self.logger.error(f"Could not read {url}", exc_info=e)

    def get_listings_from_site(self, url: str):
        """Retrieve all listings from a site
        """

        self.DRIVER.get(url)

        # accept cookies
        self._accept_cookie()

        # close popup
        self._close_popup()

        # wait a sec
        time.sleep(2)

        # retrieve listings on the site
        listings = self.DRIVER.find_elements(By.XPATH, (self.XPATH_LISTINGS))
        self.logger.info(f"{len(listings)} found")

        return [listing.get_attribute("href") for listing in listings]

    def get_info_from_all_listings(self, main_url: str):
        """Loop through all listings and get information
        """
        listing_urls = self.get_listings_from_site(main_url)

        # loop through the listings
        for listing_url in listing_urls:

            # scrape single listing
            output = self.scrape_listing(listing_url)
            if not output:
                continue

            self.db.append(output)
            self.checked_urls.append(listing_url)

    def save(self):
        """Save to CSV
        """
        data = pd.DataFrame(self.db)
        data.to_csv(self.output_filename)
        self.logger.info(f"Saved {len(data)} listings to {self.output_filename}")

    def run(self):
        self.logger.info("Starting")

        # loop through all urls
        _ = [self.get_info_from_all_listings(url) for url in self.urls]

        # save
        self.save()

        # close
        self.DRIVER.close()


if __name__ == "__main__":
    ms = marktplaats_scraper(urls=urls)
    ms.run()

