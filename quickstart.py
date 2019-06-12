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
    # prepare data
    target_users_4_copying_followers = ['Allroundraja', 'CFCricket_World', 'D11_Devill10', 'Dream11', 'Dream11Hockey', 'Dream11PKL', 'Dream11Players', 'Dream11Tips2', 'Dream11_Expert', 'Dream11_FCG', 'Dream11Help1', 'Dream11pundit', 'DreamerFantasy7', 'fanfight_app', 'Fantasy_Guruu', 'GuruDream11', 'Haiwaaaan', 'HalaPlayDotCom', 'HARMAN055_', 'IAMSANTIY224', 'india_fantasy', 'IPLExpart', 'I_am_RN_', 'KaushalKiVines', 'LeagueAdda', 'LeagueXofficial', 'MGSDREAM11', 'MyTeam_11', 'Mr360j', 'NarayananXi', 'NBAspecialist21', 'Patelvikesh664', 'PlayerzPot', 'PlayMPL', 'PredictKar', 'Royal_D11Family', 'Royalgoyal23', 'TFGfantasySport', 'WizardlyChamp', 'ballebaazi', 'cricket_dream', 'cricketgeekhere', 'cricpick', 'ddguruji', 'dream11', 'dream11champ321', 'dream11cricinfa', 'dream11sj', 'fantasykfcdream', 'fantasypower11', 'fcnupdates', 'imnandhancric', 'kingaadarsh2', 'lfcsrk', 'lootnook', 'mohitsh229', 'nikhilkomalan', 'peeyushsharmaa', 'shivakanaujia11', 'tips_dream11', 'winner_dream11']
    target_users_4_retweeting = ['ABdeVilliers17', 'henrygayle', 'harbhajan_singh', 'StarSportsIndia', 'YUVSTRONG12', 'yuzi_chahal', 'imkuldeep18', 'klrahul11', 'hardikpandya7', 'Jaspritbumrah93', 'CricketNDTV', 'virendersehwag', 'cricketworldcup', 'circleofcricket', 'ICC',  'BCCI', 'CricInformer', 'sachin_rt', 'bhogleharsha', 'cricbuzz', 'sanjaymanjrekar', 'SGanguly99', 'anilkumble1074']

    number = random.randint(2, 3)
    if len(target_users_4_copying_followers) <= number:
        random_target_users_4_copying_followers = target_users_4_copying_followers
    else:
        random_target_users_4_copying_followers = random.sample(target_users_4_copying_followers, number)

    number = random.randint(5, 20)
    if len(target_users_4_retweeting) <= number:
        random_target_users_4_retweeting = target_users_4_retweeting
    else:
        random_target_users_4_retweeting = random.sample(target_users_4_retweeting, number)

    followers, following = session.get_relationship_counts()

    # general settings
    session.set_do_follow(enabled=True, percentage=40, times=1)
    session.set_dont_include(target_users_4_copying_followers + target_users_4_retweeting)

    # activity
    if (now.day % 2 == 0 and 5 * followers < following) or following >= 7000:
        session.unfollow_all(amount=min(int(0.5*following), random.randint(40, 60)))
    # session.follow_by_list(followlist=random_target_users_4_copying_followers, times=1, sleep_delay=600, interact=False)
    session.follow_user_followers(random_target_users_4_copying_followers, amount=random.randint(10, 30))
    # session.follow_likers(random_target_users_4_copying_followers, photos_grab_amount = 2, follow_likers_per_photo = 3, randomize=True, sleep_delay=600, interact=False)
    session.welcome_dm("Thanks For Following. Happy To Connect.👍😀🙏")
    session.retweet_latest(random_target_users_4_retweeting, window_hours=1)
