import time
import logging
import os
import random
from sys import exit as clean_exit
from math import ceil

from .login_util import login_user
from .settings import Settings

from .unfollow_util  import follow_restriction
from .unfollow_util  import dm_restriction
from .unfollow_util  import follow_user

from contextlib import contextmanager
from tempfile import gettempdir

from socialcommons.print_log_writer import log_follower_num
from socialcommons.print_log_writer import log_following_num

from .util import parse_cli_args
from .util import interruption_handler
from .util import highlight_print
from .util import truncate_float
from .util import web_address_navigator
from .util import save_account_progress
from .util import get_relationship_counts

from socialcommons.time_util import sleep

from socialcommons.browser import close_browser
from socialcommons.file_manager import get_logfolder
from socialcommons.browser import set_selenium_local_session

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from socialcommons.exceptions import SocialPyError

ROW_HEIGHT = 80

class TwitterPy:
    """Class to be instantiated to use the script"""
    def __init__(self,
                 username=None,
                 password=None,
                 email=None,
                 selenium_local_session=True,
                 browser_profile_path=None,
                 page_delay=25,
                 show_logs=True,
                 headless_browser=False,
                 disable_image_load=False,
                 multi_logs=True,
                 use_firefox=False):

        cli_args = parse_cli_args()
        username = cli_args.username or username
        password = cli_args.password or password
        email = cli_args.email or email
        page_delay = cli_args.page_delay or page_delay
        headless_browser = cli_args.headless_browser or headless_browser
        disable_image_load = cli_args.disable_image_load or disable_image_load

        self.browser = None
        self.headless_browser = headless_browser
        self.use_firefox = use_firefox
        self.selenium_local_session = selenium_local_session
        self.disable_image_load = disable_image_load

        self.username = username or os.environ.get('TWITTER_USER')
        self.password = password or os.environ.get('TWITTER_PW')
        self.email = email or os.environ.get('TWITTER_EMAIL')

        Settings.profile["name"] = self.username
        self.browser_profile_path = browser_profile_path

        self.page_delay = page_delay
        self.followed = 0
        self.followed_by = 0
        self.following_num = 0

        self.follow_times = 1
        self.do_follow = False

        self.dont_include = set()
        self.white_list = set()

        self.user_interact_amount = 0
        self.user_interact_media = None
        self.user_interact_percentage = 0
        self.user_interact_random = False

        self.jumps = {
            "consequent": {"likes": 0, "comments": 0, "follows": 0, "unfollows": 0},
            "limit": {"likes": 7, "comments": 3, "follows": 5, "unfollows": 4}
        }

        self.start_time = time.time()
        # assign logger
        self.show_logs = show_logs
        Settings.show_logs = show_logs or None
        self.multi_logs = multi_logs
        self.logfolder = get_logfolder(self.username, self.multi_logs, Settings)
        self.logger = self.get_twitterpy_logger(self.show_logs)

        if self.selenium_local_session is True:
            self.set_selenium_local_session(Settings)

    def get_twitterpy_logger(self, show_logs):
        """
        Handles the creation and retrieval of loggers to avoid
        re-instantiation.
        """

        existing_logger = Settings.loggers.get(self.username)
        if existing_logger is not None:
            return existing_logger
        else:
            # initialize and setup logging system for the TwitterPy object
            logger = logging.getLogger(self.username)
            logger.setLevel(logging.DEBUG)
            file_handler = logging.FileHandler(
                '{}general.log'.format(self.logfolder))
            file_handler.setLevel(logging.DEBUG)
            extra = {"username": self.username}
            logger_formatter = logging.Formatter(
                '%(levelname)s [%(asctime)s] [TwitterPy:%(username)s]  %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(logger_formatter)
            logger.addHandler(file_handler)

            if show_logs is True:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)
                console_handler.setFormatter(logger_formatter)
                logger.addHandler(console_handler)

            logger = logging.LoggerAdapter(logger, extra)

            Settings.loggers[self.username] = logger
            Settings.logger = logger
            return logger

    def set_selenium_local_session(self, Settings):
        self.browser, err_msg = \
            set_selenium_local_session(None,
                                       None,
                                       None,
                                       self.headless_browser,
                                       self.use_firefox,
                                       self.browser_profile_path,
                                       # Replaces
                                       # browser User
                                       # Agent from
                                       # "HeadlessChrome".
                                       self.disable_image_load,
                                       self.page_delay,
                                       self.logger,
                                       Settings)
        if len(err_msg) > 0:
            raise SocialPyError(err_msg)

    def login(self):
        """Used to login the user either with the username and password"""
        if not login_user(self.browser,
                          self.username,
                          self.password,
                          self.email,
                          self.logger,
                          self.logfolder):
            message = "Wrong login data!"
            highlight_print(Settings, self.username,
                            message,
                            "login",
                            "critical",
                            self.logger)

            # self.aborting = True
        else:
            message = "Logged in successfully!"
            highlight_print(Settings, self.username,
                            message,
                            "login",
                            "info",
                            self.logger)
            # try to save account progress
            try:
                save_account_progress(Settings,
                                    self.browser,
                                    self.username,
                                    self.logger)
            except Exception:
                self.logger.warning(
                    'Unable to save account progress, skipping data update')

        self.followed_by = log_follower_num(self.browser,
                                            Settings,
                                            "https://www.twitter.com/",
                                            self.username,
                                            self.username,
                                            self.logfolder)

        self.following_num = log_following_num(self.browser,
                                            Settings,
                                            "https://www.twitter.com/",
                                            self.username,
                                            self.username,
                                            self.logfolder)
        return self

    def set_do_follow(self, enabled=False, percentage=0, times=1):
        self.follow_times = times
        self.do_follow = enabled
        # self.follow_percentage = percentage

        return self

    def set_dont_include(self, friends=None):
        """Defines which accounts should not be unfollowed"""
        # if self.aborting:
        #     return self

        self.dont_include = set(friends) or set()
        self.white_list = set(friends) or set()
        return self

    def set_user_interact(self,
                          amount=10,
                          percentage=100,
                          randomize=False,
                          media=None):
        """Define if posts of given user should be interacted"""
        # if self.aborting:
        #     return self

        self.user_interact_amount = amount
        self.user_interact_random = randomize
        self.user_interact_percentage = percentage
        self.user_interact_media = media

        return self

    def count_new_followers(self, sleep_delay=2):
        web_address_navigator(Settings, self.browser, "https://twitter.com/notifications")
        self.logger.info('Browsing my notifications')
        delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
        sleep(delay_random)
        rows = self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div > div > div > section > div > div > div > div > div > article > div > div")
        cnt = 0
        for row in rows:
            try:
                if "followed you" in row.text:
                    # self.logger.info(row.text)
                    if "others" in row.text:
                        splitted = row.text.split('others')[0].split(' ')
                        splitted = [x for x in splitted if x]
                        cnt = cnt + int(splitted[-1]) + 1
                    elif "others" in row.text:
                        cnt = cnt + 2
                    else:
                        cnt = cnt + 1
            except Exception as e:
                self.logger.error(e)
        return cnt

    def welcome_dm(self, message, sleep_delay=2):
        new_followers_cnt = self.count_new_followers()
        self.logger.info("Potential new followers: {}".format(new_followers_cnt))

        web_address_navigator(Settings, self.browser, "https://twitter.com/" + self.username + "/followers")
        rows = []
        self.logger.info('Browsing followers of {}'.format(self.username))
        delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))

        scroll_limit = 0
        try:
            while len(rows) < new_followers_cnt and scroll_limit < 10:
                scroll_limit = scroll_limit + 1
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(delay_random)
                rows = self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")
                self.logger.info("{} rows navigated".format(len(rows)))
                self.browser.execute_script("window.scrollTo(0, 0);")

            sleep(delay_random)
            rows = self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")
            self.logger.info("{} rows to be enumerated".format(len(rows)))
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(delay_random)
        except Exception as e:
            self.logger.error(e)

        user_names = []

        for i in range(0, len(rows)):
            try:
                self.browser.execute_script("window.scrollTo(0, " + str(ROW_HEIGHT*i) + ");")
                profilelink_tag = self.browser.find_element_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div:nth-child(" + str(i+1) + ") > div > div > div > div > div > div > a")
                profilelink = profilelink_tag.get_attribute('href')
                self.logger.info(profilelink)
                user_name = profilelink.split('/')[3]
                self.logger.info("Collected=> {}".format(user_name))
                user_names.append(user_name)
                sleep(delay_random*0.2)
            except Exception as e:
                self.logger.error(e)

        dm_cnt = 0
        for user_name in user_names:
            self.logger.info("Opening dm of {}".format(user_name))
            try:
                if dm_restriction("read", user_name,  self.follow_times, self.logger):
                    continue
                web_address_navigator(Settings, self.browser, "https://twitter.com/{}".format(user_name))
                mail_button = self.browser.find_element_by_css_selector("div > div > div > div > div > div > div > div > div:nth-child(1) > div > div > div > div[aria-label='Message'] > div > svg")
                (ActionChains(self.browser)
                 .move_to_element(mail_button)
                 .perform())
                sleep(delay_random)

                (ActionChains(self.browser)
                 .click()
                 .perform())
                sleep(delay_random*5)

                header_user_name_tag = self.browser.find_element_by_css_selector("div > div > div > section:nth-child(2) > div > div > div > div > div > div > div > span")
                self.logger.info(header_user_name_tag.text[1:])

                if header_user_name_tag.text[1:]==user_name:
                    textbox = self.browser.find_element_by_css_selector("div > textarea")
                    (ActionChains(self.browser)
                     .move_to_element(textbox)
                     .click()
                     .send_keys(message)
                     .perform())
                    sleep(delay_random)
    
                    (ActionChains(self.browser)
                     .send_keys(Keys.RETURN)
                     .perform())
                    sleep(delay_random)

                    self.logger.info("To: {} ".format(user_name))
                    self.logger.info("Sent: {}".format(message))
                    dm_restriction("write", user_name, None, self.logger)
                    dm_cnt = dm_cnt + 1
                else:
                    self.logger.info("header_user_name mismatch")
                self.logger.info("Total DMed in this iteration {}".format(dm_cnt))
                if dm_cnt > 5:
                    self.logger.info("Too much of same DM sent. Returning")
                    return
            except Exception as e:
                self.logger.error(e)

    def retweet_latest_from_status(self, sleep_delay=2):
        self.logger.info("Seems recent, Retweeting...")
        delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))

        for i in range(1, 5):
            sleep(delay_random)
            self.browser.execute_script("window.scrollTo(0, 200*" + str(i) + ");")
            sleep(delay_random)
            try:
                retweet_button = self.browser.find_element_by_css_selector("div > div > div > main > div > div > div > div > div > div > div > div > section > div > div > div > div:nth-child(1) > div > article > div > div:nth-child(2) > div > div > div > svg > g > path")
                (ActionChains(self.browser)
                 .move_to_element(retweet_button)
                 .perform())
                sleep(delay_random)

                (ActionChains(self.browser)
                 .click()
                 .perform())
                self.logger.info("Retweet clicked")
                sleep(delay_random)

                #TODO: This is a hack.Since retweet popup opens exact over the button this is working
                retweet_inside_popup = self.browser.find_element_by_css_selector("div > div > div > div > div > div:nth-child(2) > div > div > div > div > div:nth-child(1)")
                (ActionChains(self.browser)
                 .move_to_element(retweet_inside_popup)
                 .perform())
                sleep(delay_random)

                (ActionChains(self.browser)
                 .click()
                 .perform())
                self.logger.info("Retweet popup clicked")
                sleep(delay_random)
                break
            except Exception as e:
                self.logger.error(e)
                self.logger.info("Still not visible, scrolling down further")

    def retweet_latest_from_profile(self, sleep_delay=2):
        self.logger.info("Seems recent, Retweeting...")
        delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))

        for i in range(1, 5):
            sleep(delay_random)
            self.browser.execute_script("window.scrollTo(0, 200*" + str(i) + ");")
            sleep(delay_random)
            try:
                retweet_button = self.browser.find_element_by_css_selector("div > div > div > main > div > div > div > div > div > div > div > div > div > div > div > section > div > div > div > div > div > div > article > div > div > div > div:nth-child(2) > div > div > div:nth-child(1) > svg > g > path")
                (ActionChains(self.browser)
                 .move_to_element(retweet_button)
                 .perform())
                sleep(delay_random)

                (ActionChains(self.browser)
                 .click()
                 .perform())
                self.logger.info("Retweet clicked")
                sleep(delay_random)

                #TODO: This is a hack.Since retweet popup opens exact over the button this is working
                retweet_inside_popup = self.browser.find_element_by_css_selector("div > div > div > div > div > div:nth-child(2) > div > div > div > div > div:nth-child(1)")
                (ActionChains(self.browser)
                 .move_to_element(retweet_inside_popup)
                 .perform())
                sleep(delay_random)

                (ActionChains(self.browser)
                 .click()
                 .perform())
                self.logger.info("Retweet popup clicked")
                sleep(delay_random)
                break
            except Exception as e:
                self.logger.error(e)
                self.logger.info("Still not visible, scrolling down further")

    def search_and_retweet(self, query, sleep_delay=2):
        web_address_navigator(Settings, self.browser, "https://twitter.com/search?q=" + query.replace(' ',"%20") + "&src=typd&f=live")
        elements = self.browser.find_elements_by_css_selector("article")
        self.logger.info("Now Count = {}".format(len(elements)))
        hrefs = []
        for element in elements:
            links = element.find_elements_by_css_selector("a")
            for link in links:
                href =link.get_attribute('href')
                if '/status/' in href:
                    hrefs.append(href)
            self.logger.info("====")
        for href in hrefs:
            web_address_navigator(Settings, self.browser, href)
            self.logger.info("Retweeting => {} ".format(href))
            self.retweet_latest_from_status(sleep_delay=sleep_delay)

    def retweet_latest(self, users, window_hours=1, sleep_delay=2):
        for user in users:
            web_address_navigator(Settings, self.browser, "https://twitter.com/" + user)
            try:
                latest_tweet_time_info = self.browser.find_element_by_css_selector("div > div > div > main > div > div > div > div > div > div > div > div > div > div > div > section > div > div > div > div > div > div > article > div > div:nth-child(2) > div > div:nth-child(1) > div:nth-child(1) > a > time")
                self.logger.info(user)
                self.logger.info(latest_tweet_time_info.text)
                if "m" in latest_tweet_time_info.text:
                    self.retweet_latest_from_profile(sleep_delay)
                else:
                    if "h" in latest_tweet_time_info.text:
                        hrs = int(latest_tweet_time_info.text.strip()[:-1])
                        if hrs <= window_hours:
                            self.retweet_latest_from_profile(sleep_delay)
                        else:
                            self.logger.info("More than {} hour(s) old".format(str(hrs)))
                    else:
                        self.logger.info("Might be days old")
            except Exception as e:
                self.logger.error(e)
            self.logger.info("======")

    def get_relationship_counts(self):
        return get_relationship_counts(self.browser, self.username, self.logger)

    def visit_and_unfollow(self, profilelink, sleep_delay=2):
        try:
            web_address_navigator(Settings, self.browser,profilelink)
            self.logger.info('Visiting to unfollow: {}'.format(profilelink))
            try:
                button = self.browser.find_element_by_css_selector("div > div > div > div > div > div > div > div > div:nth-child(1) > div > div > div > div > div > div > div > span")
                if button.text.strip()=='':
                    raise Exception()
            except Exception as e:
                button = self.browser.find_element_by_css_selector("div > div > div > main > div > div > div > div > div > div > div > div > div > div:nth-child(1) > div > div > div > div:nth-child(3) > div > div > div > span > span")
                if button.text.strip()=='':
                    return False

            if button.text.strip()=='Following':
                self.logger.info('Clicking {}'.format(button.text))
                button_old_text = button.text.strip()

                (ActionChains(self.browser)
                 .move_to_element(button)#self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")[i].find_element_by_css_selector("div > div > div > div > span > span"))
                 .perform())
                delay_random = random.randint(
                            ceil(sleep_delay * 0.85),
                            ceil(sleep_delay * 1.14))
                sleep(delay_random)

                (ActionChains(self.browser)
                 .click()
                 .perform())
                delay_random = random.randint(
                            ceil(sleep_delay * 0.85),
                            ceil(sleep_delay * 1.14))
                sleep(delay_random)

                (ActionChains(self.browser)
                 .move_to_element(self.browser.find_element_by_css_selector("div > div > div > div > div > div > div > div > div > div > div:nth-child(2) > div > span > span"))
                 .perform())
                delay_random = random.randint(
                            ceil(sleep_delay * 0.85),
                            ceil(sleep_delay * 1.14))
                sleep(delay_random)

                (ActionChains(self.browser)
                 .click()
                 .perform())
                delay_random = random.randint(
                            ceil(sleep_delay * 0.85),
                            ceil(sleep_delay * 1.14))
                sleep(delay_random)

                if button_old_text == button.text.strip():
                    return False
                else:
                    self.logger.info('Button changed to {}'.format(button.text))
                    return True
            else:
                self.logger.info('Already {}'.format(button.text))
        except Exception as e:
            self.logger.error(e)
        return False

    def unfollow_users(self, skip=10, amount=20, sleep_delay=2):
        try:
            unfollowed = 0
            failed = 0
            web_address_navigator(Settings, self.browser, "https://twitter.com/" + self.username + "/following")
            rows = []
            self.logger.info('Collecting followings of {} which are to be unfollowed'.format(self.username))
            delay_random = random.randint(
                        ceil(sleep_delay * 0.85),
                        ceil(sleep_delay * 1.14))

            for i in range(0, skip):
                self.logger.info("Skipped => {} rows".format(i))
                self.browser.execute_script("window.scrollTo(0, " + str(ROW_HEIGHT*i) + ");")
                sleep(delay_random*0.03)

            sleep(delay_random)
            rows = self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")
            self.logger.info("row {} - {} to be Collected".format(skip, skip+len(rows)))

            profilelinks = []
            for i in range(0, len(rows)):
                try:
                    profilelink_tag = self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")[i].find_element_by_css_selector("div > a")
                    profilelink = profilelink_tag.get_attribute("href")
                    self.logger.info("Collected => {}".format(profilelink))
                    sleep(delay_random*0.06)
                    profilelinks.append(profilelink)
                except Exception as e:
                    self.logger.error(e)
            self.logger.info("{} links Collected to unfollow".format(len(profilelinks)))

            for profilelink in profilelinks:
                if self.visit_and_unfollow(profilelink):
                    unfollowed = unfollowed + 1
                else:
                    failed = failed + 1
                self.logger.info('unfollowed in this iteration till now: {}'.format(unfollowed))
                if unfollowed > amount:
                    self.logger.info('Unfollowed too many times this hour. Returning')
                    return
                if failed > 6:
                    self.logger.info('failed too many ({}) times. Returning'.format(failed))
                    return
        except Exception as e:
            self.logger.error(e)

    def follow_user_followers(self, users, amount, sleep_delay=2):
        followed = 0
        failed = 0
        for user in users:
            web_address_navigator(Settings, self.browser, "https://twitter.com/" + user + "/followers")
            rows = []
            self.logger.info('Browsing followers of {}'.format(user))
            try:
                while len(rows) < 10:
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    delay_random = random.randint(
                                ceil(sleep_delay * 0.85),
                                ceil(sleep_delay * 1.14))
                    sleep(delay_random)
                    rows = self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")
                    self.logger.info(len(rows))
                    self.browser.execute_script("window.scrollTo(0, 0);")
            except Exception as e:
                self.logger.error(e)

            for i, row in enumerate(rows):
                try:
                    profilelink_tag = row.find_element_by_css_selector("div > a")
                    button = row.find_element_by_css_selector("div > div > div > div > span > span")
                    profilelink = profilelink_tag.get_attribute("href")
                    self.logger.info(profilelink)
                    if button.text=='Follow':
                        self.logger.info('Clicking {}'.format(button.text))
                        button_old_text = button.text

                        (ActionChains(self.browser)
                         .move_to_element(self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")[i].find_element_by_css_selector("div > div > div > div > span > span"))
                         .perform())
                        delay_random = random.randint(
                                    ceil(sleep_delay * 0.85),
                                    ceil(sleep_delay * 1.14))
                        sleep(delay_random)

                        (ActionChains(self.browser)
                         .click()
                         .perform())
                        delay_random = random.randint(
                                    ceil(sleep_delay * 0.85),
                                    ceil(sleep_delay * 1.14))
                        sleep(delay_random)

                        if button_old_text == self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")[i].find_element_by_css_selector("div > div > div > div > span > span").text:
                            failed = failed + 1
                            self.logger.info('Failed {} times'.format(failed))
                        else:
                            followed = followed + 1
                            self.logger.info('Button changed to {}'.format(self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")[i].find_element_by_css_selector("div > div > div > div > span > span").text))
                            sleep(delay_random*3)
                    else:
                        self.logger.info('Already {}'.format(button.text))
                except Exception as e:
                    self.logger.error(e)
                    if ('The element reference of' in str(e) or 'is out of bounds of viewport' in str(e) or 'Web element reference not seen before' in str(e)):
                        self.logger.info('Breaking')
                        break
                    else:
                        failed = failed + 1
                        self.logger.info('Failed {} times'.format(failed))
                    delay_random = random.randint(
                                ceil(sleep_delay * 0.85),
                                ceil(sleep_delay * 1.14))
                    sleep(delay_random)

                self.browser.execute_script("window.scrollTo(0, " + str((i+1)*ROW_HEIGHT) + ");")
                if failed >= 6:
                    self.logger.info('Failed too many times. Something is wrong. Returning')
                    return
                self.logger.info('followed in this iteration till now: {}'.format(followed))
                if followed >= 30:
                    self.logger.info('Followed too many times this hour. Returning')
                    return

    def follow_by_list(self, followlist, times=1, sleep_delay=600,
                       interact=False):
        """Allows to follow by any scrapped list"""
        if not isinstance(followlist, list):
            followlist = [followlist]
        self.follow_times = times or 0

        followed_all = 0
        followed_new = 0
        already_followed = 0
        relax_point = random.randint(7, 14)  # you can use some plain value
        # `10` instead of this quitely randomized score
        # self.quotient_breach = False

        for acc_to_follow in followlist:
            if self.jumps["consequent"]["follows"] >= self.jumps["limit"][
                    "follows"]:
                self.logger.warning(
                    "--> Follow quotient reached its peak!\t~leaving "
                    "Follow-By-Tags activity\n")
                # reset jump counter before breaking the loop
                self.jumps["consequent"]["follows"] = 0
                # turn on `quotient_breach` to break the internal iterators
                # of the caller
                # self.quotient_breach = True if not standalone else False
                break

            if follow_restriction("read", acc_to_follow, self.follow_times,
                                  self.logger):
                self.logger.info('')
                continue

            # Take a break after a good following
            if followed_new >= relax_point:
                delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
                sleep_time = ("{} seconds".format(delay_random) if
                              delay_random < 60 else
                              "{} minutes".format(truncate_float(
                                  delay_random / 60, 2)))
                self.logger.info("Followed {} new users  ~sleeping about {}\n"
                                 .format(followed_new, sleep_time))
                sleep(delay_random)
                followed_new = 0
                relax_point = random.randint(7, 14)
                pass

            if not follow_restriction("read", acc_to_follow, self.follow_times,
                                      self.logger):
                follow_state, msg = follow_user(self.browser,
                                                "profile",
                                                self.username,
                                                acc_to_follow,
                                                None,
                                                None,
                                                self.logger,
                                                self.logfolder, Settings)
                sleep(random.randint(1, 3))

                if follow_state is True:
                    followed_all += 1
                    followed_new += 1
                    # reset jump counter after a successful follow
                    self.jumps["consequent"]["follows"] = 0

                    # if standalone:  # print only for external usage (
                    #     # internal callers have their printers)
                    #     self.logger.info(
                    #         "Total Follow: {}\n".format(str(followed_all)))

                    # Check if interaction is expected
                    if interact and self.do_like:
                        do_interact = random.randint(0,
                                                     100) <= \
                            self.user_interact_percentage
                        # Do interactions if any
                        if do_interact and self.user_interact_amount > 0:
                            original_do_follow = self.do_follow  # store the
                            # original value of `self.do_follow`
                            self.do_follow = False  # disable following
                            # temporarily cos the user is already followed
                            # above
                            self.interact_by_users(acc_to_follow,
                                                   self.user_interact_amount,
                                                   self.user_interact_random,
                                                   self.user_interact_media)
                            self.do_follow = original_do_follow  # revert
                            # back original `self.do_follow` value (either
                            # it was `False` or `True`)

                elif msg == "already followed":
                    already_followed += 1

                elif msg == "jumped":
                    # will break the loop after certain consecutive jumps
                    self.jumps["consequent"]["follows"] += 1

                sleep(1)

        # always sum up general objects regardless of the request size
        self.followed += followed_all
        # self.already_followed += already_followed
        # self.not_valid_users += not_valid_users

        return followed_all

    def live_report(self):
        """ Report live sessional statistics """

        self.logger.info('')

        stats = [self.followed]

        if self.following_num and self.followed_by:
            owner_relationship_info = (
                "On session start was FOLLOWING {} users"
                " & had {} FOLLOWERS"
                .format(self.following_num,
                        self.followed_by))
        else:
            owner_relationship_info = ''

        sessional_run_time = self.run_time()
        run_time_info = ("{} seconds".format(sessional_run_time) if
                        sessional_run_time < 60 else
                        "{} minutes".format(truncate_float(
                            sessional_run_time / 60, 2)) if
                        sessional_run_time < 3600 else
                        "{} hours".format(truncate_float(
                            sessional_run_time / 60 / 60, 2)))
        run_time_msg = "[Session lasted {}]".format(run_time_info)

        if any(stat for stat in stats):
            self.logger.info(
                "Sessional Live Report:\n"
                "\t|> FOLLOWED {} users  |  ALREADY FOLLOWED: {}\n"
                "\n{}\n{}"
                .format(self.followed,
                        owner_relationship_info,
                        run_time_msg))
        else:
            self.logger.info("Sessional Live Report:\n"
                            "\t|> No any statistics to show\n"
                            "\n{}\n{}"
                            .format(owner_relationship_info,
                                    run_time_msg))

    def end(self):
        """Closes the current session"""

        # IS_RUNNING = False
        close_browser(self.browser, False, self.logger)

        with interruption_handler():
            # write useful information
            # dump_follow_restriction(self.username,
            #                         self.logger,
            #                         self.logfolder)
            # dump_record_activity(self.username,
            #                      self.logger,
            #                      self.logfolder,
            #                      Settings)

            with open('{}followed.txt'.format(self.logfolder), 'w') \
                    as followFile:
                followFile.write(str(self.followed))

            # output live stats before leaving
            self.live_report()

            message = "Session ended!"
            highlight_print(Settings, self.username, message, "end", "info", self.logger)
            self.logger.info("\n\n")

    def run_time(self):
        """ Get the time session lasted in seconds """

        real_time = time.time()
        run_time = (real_time - self.start_time)
        run_time = truncate_float(run_time, 2)

        return run_time

@contextmanager
def smart_run(session):
    try:
        if session.login():
            yield
        else:
            print("Not proceeding as login failed")

    except (Exception, KeyboardInterrupt) as exc:
        if isinstance(exc, NoSuchElementException):
            # the problem is with a change in IG page layout
            log_file = "{}.html".format(time.strftime("%Y%m%d-%H%M%S"))
            file_path = os.path.join(gettempdir(), log_file)
            with open(file_path, "wb") as fp:
                fp.write(session.browser.page_source.encode("utf-8"))
            print("{0}\nIf raising an issue, "
                  "please also upload the file located at:\n{1}\n{0}"
                  .format('*' * 70, file_path))

        # provide full stacktrace (else than external interrupt)
        if isinstance(exc, KeyboardInterrupt):
            clean_exit("You have exited successfully.")
        else:
            raise

    finally:
        session.end()

