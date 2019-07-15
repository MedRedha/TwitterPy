"""Module only used for the login part of the script"""
# import built-in & third-party modules
import time
import pickle
from selenium.webdriver.common.action_chains import ActionChains

from socialcommons.time_util import sleep
from socialcommons.util import update_activity
from socialcommons.util import web_address_navigator
from socialcommons.util import reload_webpage
from socialcommons.util import explicit_wait
from .settings import Settings
from selenium.common.exceptions import WebDriverException

def check_authorization(browser, Settings, base_url, username, userid, method, logger, logfolder, notify=True):
    """ Check if user is NOW logged in """
    if notify is True:
        logger.info("Checking if '{}' is logged in...".format(username))
    navs = browser.find_elements_by_xpath('//div/div/div/header/div/div/div/div[1]/div[2]/nav')

    if len(navs) >= 1:
        # create cookie for username
        pickle.dump(browser.get_cookies(), open(
            '{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
        return True
    return False

def login_user(browser,
               username,
               password,
               email,
               logger,
               logfolder):
    """Logins the user with the given username and password"""
    assert username, 'Username not provided'
    assert password, 'Password not provided'

    print(username, password)
    ig_homepage = "https://www.twitter.com/login"
    web_address_navigator(browser, ig_homepage, Settings)
    cookie_loaded = False

    # try to load cookie from username
    try:
        for cookie in pickle.load(open('{0}{1}_cookie.pkl'
                                       .format(logfolder, username), 'rb')):
            browser.add_cookie(cookie)
            cookie_loaded = True
    except (WebDriverException, OSError, IOError):
        print("Cookie file not found, creating cookie...")

    # include time.sleep(1) to prevent getting stuck on google.com
    time.sleep(1)

    # changes twitter website language to english to use english xpaths
    # if switch_language:
    #     links = browser.find_elements_by_xpath('//*[@id="pageFooter"]/ul/li')
    #     for link in links:
    #         if link.get_attribute('title') == "English (UK)":
    #             click_element(browser, Settings, link)

    web_address_navigator(browser, ig_homepage, Settings)
    reload_webpage(browser, Settings)

    # if user is still not logged in, then there is an issue with the cookie
    # so go create a new cookie..

    # cookie has been LOADED, so the user SHOULD be logged in
    # check if the user IS logged in
    if cookie_loaded:
        login_state = check_authorization(browser, Settings,
                                        "https://www.twitter.com/login",
                                        username,
                                        None,
                                        "activity counts",
                                        logger,
                                        logfolder,
                                        True)
        print('check_authorization:', login_state)
        if login_state is True:
            # dismiss_notification_offer(browser, logger)
            return True
        else:
            print("Issue with cookie for user {}. Creating "
                  "new cookie...".format(username))

    input_username_XP = '//*[@id="page-container"]/div/div[1]/form/fieldset/div[1]/input'
    input_username = browser.find_element_by_xpath(input_username_XP)

    print('moving to input_username')
    print('entering input_username')
    #email login doesn't reprompt
    (ActionChains(browser)
     .move_to_element(input_username)
     .click()
     .send_keys(email)
     .perform())

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity(Settings)

    sleep(1)

    #  password
    input_password = browser.find_elements_by_xpath('//*[@id="page-container"]/div/div[1]/form/fieldset/div[2]/input')

    if not isinstance(password, str):
        password = str(password)

    print('entering input_password')
    (ActionChains(browser)
     .move_to_element(input_password[0])
     .click()
     .send_keys(password)
     .perform())

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity(Settings)

    sleep(1)

    print('submitting login_button')
    login_button = browser.find_element_by_xpath('//*[@id="page-container"]/div/div[1]/form/div[2]/button')

    (ActionChains(browser)
     .move_to_element(login_button)
     .click()
     .perform())

    # update server calls
    update_activity(Settings)

    sleep(1)

    # dismiss_get_app_offer(browser, logger)
    # dismiss_notification_offer(browser, logger)

    # if bypass_suspicious_attempt is True:
    #     bypass_suspicious_login(browser, bypass_with_mobile)

    # wait until page fully load
    explicit_wait(browser, "PFL", [], logger, 5)

    # Check if user is logged-in (If there's two 'nav' elements)
    login_state = check_authorization(browser, Settings,
                                    "https://www.twitter.com/login",
                                    username,
                                    None,
                                    "activity counts",
                                    logger,
                                    logfolder,
                                    True)
    print('check_authorization again:', login_state)
    return login_state
    # if login_state is True:
    # navs = browser.find_elements_by_xpath('//div/div/div/header/div/div/div/div[1]/div[2]/nav')

    # if len(navs) >= 1:
    #     # create cookie for username
    #     print('Logged in')
    #     pickle.dump(browser.get_cookies(), open(
    #         '{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
    #     return True
    # else:
    #     return False



