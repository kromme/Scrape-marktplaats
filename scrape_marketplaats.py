# coding: utf-8

import time
import datetime
import logging
import pandas as pd
from selenium import webdriver

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
        webdriver_path: str = "chromedriver.exe",
        output_filename: str = "output.csv",
    ):
        self.urls = urls
        self.output_filename = output_filename

        # define logger
        self._define_logger()

        # define self.DRIVER
        self.DRIVER = webdriver.Chrome(webdriver_path)

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
        self.XPATH_PRICE = ".//span[@class='price ']"
        self.XPATH_TITLE = ".//h1[@class='title']"
        self.XPATH_DESCRIPTION = ".//div[@id='vip-ad-description']"
        self.XPATH_SINCE = ".//span[@id='displayed-since']"
        self.XPATH_MOTORS = ".//a[@class='mp-Listing-coverLink']"

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

    def _accept_cookie(self):
        """Accepts cookies
        """
        try:
            self.DRIVER.find_element_by_xpath(self.XPATH_COOKIE).click()
            self.logger.info("Cookie accepted")
        except:
            pass

    def _close_popup(self):
        """Close Popup
        """
        try:
            self.DRIVER.find_element_by_xpath(self.XPATH_POPUP).click()
            self.logger.info("Popup closed")
        except:
            pass

    def scrape_motor(self, url: str):
        """Scrape a single motor
        """

        # sleep a bit to fool MP
        time.sleep(random.randint(2, 9))

        try:
            # go to url
            self.DRIVER.get(url)

            # get bids
            bids = [
                bid.text for bid in self.DRIVER.find_elements_by_xpath(self.XPATH_BID)
            ]
            max_bid = "NA" if len(bids) == 0 else bids[0]

            # get bids dates
            bids_date = [
                date.text
                for date in self.DRIVER.find_elements_by_xpath(self.XPATH_BIDDATE)
            ]
            max_bid_date = "NA" if len(bids_date) == 0 else bids_date[0]

            # get info from table
            table = ""
            try:
                table += self.DRIVER.find_element_by_xpath(
                    self.XPATH_FIRSTCOLUMN
                ).text.replace("\n", "|")
            except:
                table += ""

            try:
                table += "|" + self.DRIVER.find_element_by_xpath(
                    self.XPATH_SECONDCOLUMN
                ).text.replace("\n", "|")
            except:
                table += ""

            # gather
            output = {
                "price": self.DRIVER.find_element_by_xpath(
                    self.XPATH_PRICE
                ).text.replace(";", "|"),
                "title": self.DRIVER.find_element_by_xpath(
                    self.XPATH_TITLE
                ).text.replace(";", "|"),
                "description": self.DRIVER.find_element_by_xpath(self.XPATH_DESCRIPTION)
                .text.replace("\n", ".")
                .replace(";", "|"),
                "table": table,
                "max_bid": max_bid,
                "max_bid_date": max_bid_date,
                "motor_url": self.DRIVER.current_url,
                "bids": bids,
                "bids_date": bids_date,
                "since": self.DRIVER.find_element_by_xpath(self.XPATH_SINCE).text,
            }
            return output

        except Exception as e:
            self.logger.error(f"Could not read {url}", exc_info=e)

    def get_motors_from_site(self, url: str):
        """Retrieve all motors from a site
        """

        self.DRIVER.get(url)

        # accept cookies
        self._accept_cookie()

        # close popup
        self._close_popup()

        # wait a sec
        time.sleep(2)

        # retrieve motors on the site
        motors = self.DRIVER.find_elements_by_xpath(self.XPATH_MOTORS)
        self.logger.info(f"{len(motors)} found")

        return [motor.get_attribute("href") for motor in motors]

    def get_info_from_all_motors(self, main_url: str):
        """Loop through all motors and get information
        """
        motor_urls = self.get_motors_from_site(main_url)

        # loop through the motors
        for motor_url in motor_urls:

            # scrape single motor
            output = self.scrape_motor(motor_url)
            if not output:
                continue

            self.db.append(output)
            self.checked_urls.append(motor_url)

    def save(self):
        """Save to CSV
        """
        data = pd.DataFrame(self.db)
        data.to_csv(self.output_filename)
        self.logger.info(f"Saved {len(data)} motors to {self.output_filename}")

    def run(self):
        self.logger.info("Starting")

        # loop through all urls
        _ = [self.get_info_from_all_motors(url) for url in self.urls]

        # save
        self.save()

        # close
        self.DRIVER.close()


if __name__ == "__main__":
    ms = marktplaats_scraper(urls=urls)
    ms.run()

