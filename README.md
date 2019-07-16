# TwitterPy


## Installation:
It is recomended to use via pyenv We will be supporting python 3.6.0 and above going forward

```
pip install --upgrade pip
curl https://pyenv.run | bash
curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
pyenv install 3.6.0
pyenv local 3.6.0
pip install -r requirements.txt
```

##  APIs:
  - [Follow usernames given by a list](#Follow-usernames-given-by-a-list)
  - [Follow followers of each of the users from a list](#Follow-followers-of-each-of-the-users-from-a-list)
  - [Unfollow users](#Unfollow-users)
  - [Send a welcome message](#Send-a-welcome-message)
  - [Retweet the lastest tweet for each of the given users](#Retweet-the-lastest-tweet-for-each-of-the-given-users)
  - [Search and Retweet](#Search-and-Retweet)

### Follow usernames given by a list
 
```python

 session = TwitterPy()

 with smart_run(session):
     session.follow_by_list(followlist=my_users_list, 
                    times=1, 
                    sleep_delay=600, 
                    interact=False)
 ```

### Follow followers of each of the users from a list

```python

 session = TwitterPy()

 with smart_run(session):
     session.follow_user_followers(my_users_list,
                                  amount=random.randint(30, 60))
 ```
 
### Unfollow users

```python

 session = TwitterPy()

 with smart_run(session):
     session.unfollow_users(amount=random.randint(30, 60))
 ```
 
### Send a welcome message

```python

 session = TwitterPy()

 with smart_run(session):
     session.welcome_dm("Hello")
 ```


### Retweet the lastest tweet for each of the given users

```python

 session = TwitterPy()

 with smart_run(session):
     session.retweet_latest(self, users_list, window_hours=1, sleep_delay=2)
 ```


### Search and Retweet

```python

 session = TwitterPy()

 with smart_run(session):
     session.search_and_retweet(self, query="Retweet to win", sleep_delay=2)
 ```
 
## How to run:

 -  modify `quickstart.py` according to your requirements
 -  `python quickstart.py -u <my_twitter_username> -p <mypssword>`


## How to schedule as a job:

```bash
    */10 * * * * bash /path/to/TwitterPy/run_githubpy_only_once_for_mac.sh /path/to/TwitterPy/quickstart.py $USERNAME $PASSWORD
```

## Help build socialbotspy
Check out this short guide on [how to start contributing!](https://github.com/InstaPy/instapy-docs/blob/master/CONTRIBUTORS.md).

