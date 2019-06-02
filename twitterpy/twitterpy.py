import time
import logging
import os
import random
from sys import exit as clean_exit
from math import ceil

from .login_util import login_user
from .settings import Settings

from .unfollow_util  import follow_restriction
# from .unfollow_util  import unfollow_user
from .unfollow_util  import follow_user

from contextlib import contextmanager
from tempfile import gettempdir

from socialcommons.print_log_writer import log_follower_num
from socialcommons.print_log_writer import log_following_num

from socialcommons.util import parse_cli_args
from socialcommons.util import interruption_handler
from socialcommons.util import highlight_print
from socialcommons.util import truncate_float
from socialcommons.util import web_address_navigator

from socialcommons.time_util import sleep

from socialcommons.browser import close_browser
from socialcommons.file_manager import get_workspace
from socialcommons.file_manager import get_logfolder
from socialcommons.browser import set_selenium_local_session

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

from socialcommons.exceptions import SocialPyError

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

        TWITTERPY_IS_RUNNING = True
        # workspace must be ready before anything
        if not get_workspace(Settings):
            raise SocialPyError(
                "Oh no! I don't have a workspace to work at :'(")

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
        # self.switch_language = True
        self.followed = 0
        self.already_followed = 0
        self.followed_by = 0
        self.following_num = 0

        self.follow_times = 1
        self.do_follow = False
        self.follow_percentage = 0

        self.liked_img = 0
        self.already_liked = 0

        self.dont_include = set()
        self.white_list = set()

        self.user_interact_amount = 0
        self.user_interact_media = None
        self.user_interact_percentage = 0
        self.user_interact_random = False

        self.max_followers = None   # 90000
        self.max_following = None   # 66834
        self.min_followers = None   # 35
        self.min_following = None   # 27
        self.max_posts = None
        self.min_posts = None

        self.quotient_breach = False
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
                '%(levelname)s [%(asctime)s] [%(username)s]  %(message)s',
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

            self.aborting = True
        else:
            message = "Logged in successfully!"
            highlight_print(Settings, self.username,
                            message,
                            "login",
                            "info",
                            self.logger)
            # try to save account progress
            try:
                save_account_progress(self.browser,
                                    "https://www.twitter.com/",
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
        self.follow_percentage = percentage

        return self

    def set_dont_include(self, friends=None):
        """Defines which accounts should not be unfollowed"""
        if self.aborting:
            return self

        self.dont_include = set(friends) or set()
        self.white_list = set(friends) or set()

        return self

    def set_relationship_bounds(self,
                                enabled=None,
                                potency_ratio=None,
                                delimit_by_numbers=None,
                                min_posts=None,
                                max_posts=None,
                                max_followers=None,
                                max_following=None,
                                min_followers=None,
                                min_following=None):
        """Sets the potency ratio and limits to the provide an efficient
        activity between the targeted masses"""

        self.potency_ratio = potency_ratio if enabled is True else None
        self.delimit_by_numbers = delimit_by_numbers if enabled is True else \
            None

        self.max_followers = max_followers
        self.min_followers = min_followers

        self.max_following = max_following
        self.min_following = min_following

        self.min_posts = min_posts if enabled is True else None
        self.max_posts = max_posts if enabled is True else None

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

    # def follow_user(self, browser, track, login, userid_to_follow, button, blacklist,
    #                 logger, logfolder, Settings):
    #     """ Follow a user either from the profile page or post page or dialog
    #     box """
    #     # list of available tracks to follow in: ["profile", "post" "dialog"]

    #     # check action availability
    #     if quota_supervisor(Settings, "follows") == "jump":
    #         return False, "jumped"

    #     if track in ["profile", "post"]:
    #         if track == "profile":
    #             # check URL of the webpage, if it already is user's profile
    #             # page, then do not navigate to it again
    #             user_link = "https://www.twitter.com/{}/".format(userid_to_follow)
    #             web_address_navigator( browser, user_link, Settings)

    #         # find out CURRENT following status
    #         following_status, follow_button = \
    #             get_following_status(browser,
    #                                 track,
    #                                 login,
    #                                 userid_to_follow,
    #                                 None,
    #                                 logger,
    #                                 logfolder)
    #         if following_status in ["Follow", "Follow Back"]:
    #             click_visibly(browser, Settings, follow_button)  # click to follow
    #             follow_state, msg = verify_action(browser, "follow", track, login,
    #                                             userid_to_follow, None, logger,
    #                                             logfolder)
    #             if follow_state is not True:
    #                 return False, msg

    #         elif following_status in ["Following", "Requested"]:
    #             if following_status == "Following":
    #                 logger.info(
    #                     "--> Already following '{}'!\n".format(userid_to_follow))

    #             elif following_status == "Requested":
    #                 logger.info("--> Already requested '{}' to follow!\n".format(
    #                     userid_to_follow))

    #             sleep(1)
    #             return False, "already followed"

    #         elif following_status in ["Unblock", "UNAVAILABLE"]:
    #             if following_status == "Unblock":
    #                 failure_msg = "user is in block"

    #             elif following_status == "UNAVAILABLE":
    #                 failure_msg = "user is inaccessible"

    #             logger.warning(
    #                 "--> Couldn't follow '{}'!\t~{}".format(userid_to_follow,
    #                                                         failure_msg))
    #             return False, following_status

    #         elif following_status is None:
    #             # TODO:BUG:2nd login has to be fixed with userid of loggedin user
    #             sirens_wailing, emergency_state = emergency_exit(browser, Settings, "https://www.twitter.com", login,
    #                                                             login, logger, logfolder)
    #             if sirens_wailing is True:
    #                 return False, emergency_state

    #             else:
    #                 logger.warning(
    #                     "--> Couldn't unfollow '{}'!\t~unexpected failure".format(
    #                         userid_to_follow))
    #                 return False, "unexpected failure"
    #     elif track == "dialog":
    #         click_element(browser, Settings, button)
    #         sleep(3)

    #     # general tasks after a successful follow
    #     logger.info("--> Followed '{}'!".format(userid_to_follow.encode("utf-8")))
    #     update_activity('follows', Settings)

    #     # get user ID to record alongside username
    #     user_id = get_user_id(browser, track, userid_to_follow, logger)

    #     logtime = datetime.now().strftime('%Y-%m-%d %H:%M')
    #     log_followed_pool(login, userid_to_follow, logger,
    #                     logfolder, logtime, user_id)

    #     follow_restriction("write", userid_to_follow, None, logger)

    #     # if blacklist['enabled'] is True:
    #     #     action = 'followed'
    #     #     add_user_to_blacklist(userid_to_follow,
    #     #                         blacklist['campaign'],
    #     #                         action,
    #     #                         logger,
    #     #                         logfolder)

    #     # get the post-follow delay time to sleep
    #     naply = get_action_delay("follow", Settings)
    #     sleep(naply)
    #     return True, "success"

    def follow_user_followers(self, users, amount, sleep_delay=6):
        followed = 0
        failed = 0
        for user in users:
            web_address_navigator(self.browser, "https://twitter.com/" + user + "/followers", Settings)
            rows = []
            print('Browsing followers of', user)
            while len(rows) < 10:
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                delay_random = random.randint(
                            ceil(sleep_delay * 0.85),
                            ceil(sleep_delay * 1.14))
                sleep(delay_random)
                rows = self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")
                print(len(rows))

            for jc, row in enumerate(rows):
                try:
                    profilelink = row.find_element_by_css_selector("div > a")
                    button = row.find_element_by_css_selector("div > div > div > div > span > span")
                    print(profilelink.get_attribute("href"))
                    if button.text=='Follow':
                        print('Clicking', button.text)
                        button_old_text = button.text

                        (ActionChains(self.browser)
                         .move_to_element(self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")[jc].find_element_by_css_selector("div > div > div > div > span > span"))
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

                        if button_old_text == self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")[jc].find_element_by_css_selector("div > div > div > div > span > span").text:
                            failed = failed + 1
                            print('Failed {} times'.format(failed))
                        else:
                            followed = followed + 1
                            print('Button changed to', self.browser.find_elements_by_css_selector("div > div > div > main > div > div > div > div > div > div > div:nth-child(2) > section > div > div > div > div")[jc].find_element_by_css_selector("div > div > div > div > span > span").text)
                    else:
                        print('Already', button.text)
                    self.browser.execute_script("window.scrollTo(0, " + str(jc+1) + "*70);")
                    if failed >= 3:
                        return
                except Exception as e:
                    print(e)
                    delay_random = random.randint(
                                ceil(sleep_delay * 0.85),
                                ceil(sleep_delay * 1.14))
                    sleep(delay_random)
            print('followed in this iteration till now:', followed)

    def follow_by_list(self, followlist, times=1, sleep_delay=600,
                       interact=False):
        """Allows to follow by any scrapped list"""
        if not isinstance(followlist, list):
            followlist = [followlist]

        # if self.aborting:
        #     self.logger.info(">>> self aborting prevented")
        #     # return self

        # standalone means this feature is started by the user
        # standalone = True if "follow_by_list" not in \
        #                      self.internal_usage.keys() else False
        # skip validation in case of it is already accomplished
        # users_validated = True if not standalone and not \
        #     self.internal_usage["follow_by_list"]["validate"] else False

        self.follow_times = times or 0

        followed_all = 0
        followed_new = 0
        already_followed = 0
        # not_valid_users = 0

        # hold the current global values for differentiating at the end
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        # commented_init = self.commented
        # inap_img_init = self.inap_img

        relax_point = random.randint(7, 14)  # you can use some plain value
        # `10` instead of this quitely randomized score
        self.quotient_breach = False

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
                print('')
                continue

            # if not users_validated:
            #     # Verify if the user should be followed
            #     validation, details = self.validate_user_call(acc_to_follow)
            #     if validation is not True or acc_to_follow == self.username:
            #         self.logger.info(
            #             "--> Not a valid user: {}".format(details))
            #         not_valid_users += 1
            #         continue

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

        # if standalone:# print only for external usage (internal callers
        #     # have their printers)
        #     self.logger.info("Finished following by List!\n")
        #     # print summary
        #     self.logger.info("Followed: {}".format(followed_all))
        #     self.logger.info("Already followed: {}".format(already_followed))
        #     self.logger.info("Not valid users: {}".format(not_valid_users))

        #     if interact is True:
        #         print('')
        #         # find the feature-wide action sizes by taking a difference
        #         liked = (self.liked_img - liked_init)
        #         already_liked = (self.already_liked - already_liked_init)
        #         commented = (self.commented - commented_init)
        #         inap_img = (self.inap_img - inap_img_init)

        #         # print the summary out of interactions
        #         self.logger.info("Liked: {}".format(liked))
        #         self.logger.info("Already Liked: {}".format(already_liked))
        #         self.logger.info("Commented: {}".format(commented))
        #         self.logger.info("Inappropriate: {}".format(inap_img))

        # always sum up general objects regardless of the request size
        self.followed += followed_all
        self.already_followed += already_followed
        # self.not_valid_users += not_valid_users

        return followed_all

    def live_report(self):
        """ Report live sessional statistics """

        print('')

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

        IS_RUNNING = False
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
            print("\n\n")

    def run_time(self):
        """ Get the time session lasted in seconds """

        real_time = time.time()
        run_time = (real_time - self.start_time)
        run_time = truncate_float(run_time, 2)

        return run_time

@contextmanager
def smart_run(session):
    try:
        session.login()
        yield

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

