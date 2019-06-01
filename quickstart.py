""" Quickstart script for TwitterPy usage """

# imports
from twitterpy import TwitterPy
from twitterpy import smart_run
from socialcommons.file_manager import set_workspace
from twitterpy import settings

import random

# set workspace folder at desired location (default is at your home folder)
set_workspace(settings.Settings, path=None)

# get an TwitterPy session!
session = TwitterPy()

with smart_run(session):
    """ Activity flow """
    # # general settings
    # session.set_dont_include(["friend1", "friend2", "friend3"])

    # activity
    # session.like_by_tags(["natgeo"], amount=10)

    session.set_relationship_bounds(enabled=True,
                                    potency_ratio=None,
                                    delimit_by_numbers=True,
                                    max_followers=7500,
                                    max_following=3000,
                                    min_followers=25,
                                    min_following=25,
                                    min_posts=1)

    session.set_user_interact(amount=3, randomize=True, percentage=80,
                              media='Photo')
    # session.set_do_like(enabled=True, percentage=90)
    session.set_do_follow(enabled=True, percentage=40, times=1)
    targets = ['XHNews', 'Arsenal', 'BarackObama', 'TheEllenShow']
    number = random.randint(3, 5)
    random_targets = targets

    if len(targets) <= number:
        random_targets = targets
    else:
        random_targets = random.sample(targets, number)

    session.follow_by_list(followlist=random_targets, times=1, sleep_delay=600, interact=False)

    session.follow_user_followers(random_targets,
                                  amount=random.randint(30, 60))

    # session.follow_likers(random_targets, photos_grab_amount = 2, follow_likers_per_photo = 3, randomize=True, sleep_delay=600, interact=False)

