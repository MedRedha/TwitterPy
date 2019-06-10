""" Quickstart script for TwitterPy usage """

# imports
from twitterpy import TwitterPy
from twitterpy import smart_run
from socialcommons.file_manager import set_workspace
from twitterpy import settings

import random
import datetime
now = datetime.datetime.now()

# set workspace folder at desired location (default is at your home folder)
set_workspace(settings.Settings, path=None)

# get an TwitterPy session!
session = TwitterPy(use_firefox=True)

with smart_run(session):
    """ Activity flow """
    # general settings
    target_users = ['Allroundraja', 'CFCricket_World', 'D11_Devill10', 'Dream11Hockey', 'Dream11PKL', 'Dream11Players', 'Dream11Tips2', 'Dream11_Expert', 'Dream11_FCG', 'Dream11Help1', 'Dream11pundit', 'DreamerFantasy7', 'Fantasy_Guruu', 'GuruDream11', 'Haiwaaaan', 'HalaPlayDotCom', 'HARMAN055_', 'IAMSANTIY224', 'IPLExpart', 'I_am_RN_', 'LeagueAdda', 'LeagueXofficial', 'MGSDREAM11', 'MyTeam_11', 'Mr360j', 'NarayananXi', 'NBAspecialist21', 'Patelvikesh664', 'PlayerzPot', 'PlayMPL', 'PredictKar', 'Royal_D11Family', 'Royalgoyal23', 'TFGfantasySport', 'WizardlyChamp', 'ballebaazi', 'cricket_dream', 'cricketgeekhere', 'cricpick', 'ddguruji', 'dream11', 'dream11champ321', 'dream11cricinfa', 'dream11sj', 'fantasykfcdream', 'fantasypower11', 'fcnupdates', 'imnandhancric', 'kingaadarsh2', 'lfcsrk', 'lootnook', 'mohitsh229', 'peeyushsharmaa', 'shivakanaujia11', 'tips_dream11', 'winner_dream11']
    session.set_dont_include(target_users)

    # activity
    # session.like_by_tags(["natgeo"], amount=10)

    # session.set_relationship_bounds(enabled=True,
    #                                 potency_ratio=None,
    #                                 delimit_by_numbers=True,
    #                                 max_followers=7500,
    #                                 max_following=3000,
    #                                 min_followers=25,
    #                                 min_following=25,
    #                                 min_posts=1)

    session.set_user_interact(amount=3, randomize=True, percentage=80, media='Photo')
    # session.set_do_like(enabled=True, percentage=90)
    session.set_do_follow(enabled=True, percentage=40, times=1)
    number = random.randint(2, 3)
    random_target_users = target_users

    if len(target_users) <= number:
        random_target_users = target_users
    else:
        random_target_users = random.sample(target_users, number)

    followers, following = session.get_relationship_counts()

    if (now.day % 2 == 0 and 5 * followers < following) or following >= 7000:
        session.unfollow_all(amount=min(int(0.5*following), random.randint(40, 60)))

    # session.follow_by_list(followlist=random_target_users, times=1, sleep_delay=600, interact=False)

    session.follow_user_followers(random_target_users, amount=random.randint(10, 30))

    # session.follow_likers(random_target_users, photos_grab_amount = 2, follow_likers_per_photo = 3, randomize=True, sleep_delay=600, interact=False)

    session.welcome_dm("Thanks For Following. Happy To Connect.👍😀🙏")
