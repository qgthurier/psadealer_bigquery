# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 11:33:58 2014

@author: qgthurier
"""

import string 
import random
pwd_list = [] 
punctuation = string.punctuation.replace(",","").replace("'","").replace("\"","") # remove some characters to make the csv uplaod safer
characters = string.ascii_letters + punctuation + string.digits 
users_file = raw_input("enter the file name for users accounts: ").strip()
credentials_file = raw_input("enter the file name for the credentials file: ").strip()
users = open(users_file)
credentials =  open(credentials_file, 'w')
credentials.write('login,password,dealer')
tot = 0
for l in users.readlines():
    tot += 1
    values = l.strip().split(',') 
    user_password = "".join(random.choice(characters) for x in range(10))
    while user_password in pwd_list:
        user_password = "".join(random.choice(characters) for x in range(10))
    pwd_list.append(user_password)
    user_login = values[0].strip()
    url = values[1].strip() # remove last carriage return character
    user_dealer = url.split("=")[1].strip()
    credentials.write('\n' + user_login + ',' + user_password + ',' + user_dealer) 
print str(tot) + ' credentials have been written into ' + credentials_file