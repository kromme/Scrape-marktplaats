# coding: utf-8

import time
import random
import datetime
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException


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
        headless: bool = False,
        proxyNo: int = 0
    ):
        self.urls = urls
        self.output_filename = output_filename
        self.proxies = pd.DataFrame()
        self.use_proxy = use_proxy
        self.headless = headless
        self.proxyNo = proxyNo

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
        self.XPATH_BID = ".//div[@class='BiddingList-content']"
        self.XPATH_BIDDATE = ".//span[@class='BiddingList-date']"
        self.XPATH_FIRSTCOLUMN = (
            ".//table[@class='first-column attribute-table single-value-attributes']"
        )
        self.XPATH_SECONDCOLUMN = (
            ".//table[@class='second-column attribute-table single-value-attributes']"
        )
        self.XPATH_PRICE = "//*[@id='listing-root']/div/div[2]/div[1]"
        self.XPATH_TITLE = "//*[@id='listing-root']/div/header/h1"
        self.XPATH_DESCRIPTION = "//div[@class='block-wrapper-s Description-root']"
        self.XPATH_SINCE = "//*[@id='listing-root']/div/div[3]/span[3]/span"
        self.XPATH_MPID = "//*[@id='report-root']/div/span"
        self.XPATH_LISTINGS = ".//a[contains(@class, 'hz-Listing-coverLink')]"

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

        if self.headless:
            self.logger.info(f'Starting the browser headless {self.headless}')
            self.options.add_argument("-headless")

        return webdriver.Firefox(options=self.options,
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
        
        self.options.set_preference("general.useragent.override", ua)
        self.logger.info(f'User agent set to {ua}')


    def _set_profile(self):
        """Create a profile for FF
        """
        self.options = Options()        
        # to make sure we can close the windows: https://stackoverflow.com/questions/45510338/selenium-webdriver-3-4-0-geckodriver-0-18-0-firefox-which-combination-w
        self.options.set_preference("browser.tabs.remote.autostart", False)
        self.options.set_preference("browser.tabs.remote.autostart.1", False)
        self.options.set_preference("browser.tabs.remote.autostart.2", False)

        # turn off auto update
        self.options.set_preference('app.update.auto',False)
        self.options.set_preference('app.update.enabled',False)
        self.options.set_preference('app.update.silent',False)
        
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
        self.options.set_preference("network.proxy.type", 1)
        self.options.set_preference("network.proxy.http", proxy)
        self.options.set_preference("network.proxy.http_port", port)
        self.options.set_preference("network.proxy.ssl", proxy)
        self.options.set_preference("network.proxy.ssl_port", port)
        self._change_useragent()
        
        self.logger.info(f'Proxy change to {proxy}:{port}')


    def _get_proxy_list(self):
        """Get list of proxies we can use
        """

        # go to page
        self.DRIVER.get('https://www.sslproxies.org/')
                
        # get table results
        table = self.DRIVER.find_element(By.XPATH, "/html/body/section[1]/div/div[2]/div/table")

        rows = table.text.split('\n')[1:80]
        self.DRIVER.close()
        
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

        while not success:
            self.logger.info(f'Trying proxy number {self.proxyNo}')
            self._change_proxy(proxyNo = self.proxyNo)
            
            # start driver
            driver = self.get_driver()
            
            try:
                driver.set_page_load_timeout(30)
                # go to duckduckgo to check ip
                driver.get('https://duckduckgo.com/?q=my+ip&t=hb&ia=answer')
                # wait for ip
                wait = WebDriverWait(driver,10)
                wait.until(lambda driver: driver.find_element(By.CLASS_NAME, 'zci__body'))
                ip = driver.find_element(By.CLASS_NAME, 'zci__body').text
            except TimeoutException as e:
                print("TimeoutException has been thrown. " + str(e))
                self.proxyNo += 1

                driver.close()
                if self.proxyNo >= 79:
                    break
                self.find_proxy()
            except WebDriverException as e:
                print("WebDriverException has been thrown. " + str(e))
                self.proxyNo += 1
                
                driver.close()
                if self.proxyNo >= 79:
                    break
                self.find_proxy()

            try:
                driver.set_page_load_timeout(30)
                # if that works, check if MP is reachable
                driver.get('https://www.marktplaats.nl')
            except TimeoutException as e:
                print("TimeoutException has been thrown requesting marktplaats.nl. " + str(e))
                self.proxyNo += 1
                
                driver.close()
                if self.proxyNo >= 79:
                    break
                self.find_proxy()
            except WebDriverException as e:
                print("WebDriverException has been thrown. " + str(e))
                self.proxyNo += 1
                
                driver.close()
                if self.proxyNo >= 79:
                    break
                self.find_proxy()

            # check if proxy isnt blocked. other go to except.
            if not ('blocked' in driver.title or 'error' in driver.title.lower()):
                self.proxyNo += 1
                
                driver.close()
                if self.proxyNo >= 79:
                    break
                self.find_proxy()
                
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

            driver = self.get_driver()
            
            try:
                driver.set_page_load_timeout(30)
                # go to url
                driver.get(url)

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

            except TimeoutException as e:
                print("TimeoutException has been thrown. " + str(e))
                self.proxyNo += 1

                driver.close()
                self.find_proxy()
            except WebDriverException as e:
                print("WebDriverException has been thrown. " + str(e))
                self.proxyNo += 1
                
                driver.close()
                self.find_proxy()

            return output

        except Exception as e:
            self.logger.error(f"Could not read {url}", exc_info=e)


    def get_listings_from_site(self, url: str):
        """Retrieve all listings from a site
        """
        driver = self.get_driver()

        try:
            driver.set_page_load_timeout(30)
            # go to duckduckgo to check ip
            driver.get(url)
            # accept cookies
            self._accept_cookie()

            # close popup
            self._close_popup()

            # wait a sec
            time.sleep(2)

            # retrieve listings on the site
            listings = self.DRIVER.find_elements(By.XPATH, (self.XPATH_LISTINGS))
            self.logger.info(f"{len(listings)} found")

        except TimeoutException as e:
            print("TimeoutException has been thrown. " + str(e))
            self.proxyNo += 1

            driver.close()
            self.find_proxy()
        except WebDriverException as e:
            print("WebDriverException has been thrown. " + str(e))
            self.proxyNo += 1
            
            driver.close()
            self.find_proxy()

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

