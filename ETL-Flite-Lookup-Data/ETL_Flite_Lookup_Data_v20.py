#flite api call to generate creative id lookup table for specified campaigns
#writes to a csv to hard disk
#copies file to axiom's sftp server

#written by Smartcom MediaVest Group
#7/17/2014


'''
notes:
-oauth credentials are associated with "StarcomMG" organization in the flite console
-guids are associated with campaigns in the flite interface
-flite reps sent both guids and oauth creds
-Shawn DeLosReyes <shawn.delosreyes@flite.com>
-Lev Pevzner <lev.pevzner@flite.com>
'''


#import libs
import requests
from requests_oauthlib import OAuth1
import time
from datetime import date, timedelta
import csv
import paramiko

#set oauth api credentials
#specific to the fabric care organization in flite's system
auth = OAuth1(
	'oyn3xhresbffqqwfbk9zxtx6ibj8l93taniqgkatd4abqw2knftmhzgahgnapxevzsa87dyjxbcwxyfjgstr6xgrnvvf5vqf',
	'kHPJw5NNKSwKrdGNACqgYKF4Gy6yJCZ4QXW0njFlRCQiWEhBg6ixcDv2WrtnMbP9',
   'oyn3xhresbffqqwfbk9zxtx6ibj8l93taniqgkatd4abqw2knftmhzgahgnapxevzsa87dyjxbcwxyfjgstr6xgrnvvf5vqf', 
   'kHPJw5NNKSwKrdGNACqgYKF4Gy6yJCZ4QXW0njFlRCQiWEhBg6ixcDv2WrtnMbP9'
	)


#define campaigns & their guids
#@guid_dict = dict([("tidepodsfree", "78fb561d-ab39-462d-a79e-ccb0d2644e96"),
#						("tidevariant","a489f4bb-3a61-451e-9a8d-b3567cea516c")])


#define a local path for file mgt prior to sftp upload
localpath = 'C:\\Users\\orrwatso\\Documents\\Data-Sources\\Flite\\'

def get_ad_ids(auth):
	url = "http://api.flite.com/rr/v1.0/data/fetch/ad/"
	data_url = url 
	ad_data = requests.get(data_url, auth=auth).json()

	return ad_data

#iterate over creative_lookup()
def compile_campaigns():
	print('compiling ads lookup...')
	final_table = []
	ads = get_ad_ids(auth)

	for adInfo in ads.get('resources'):
		final_table.append([adInfo['name'],adInfo['guid']])
	return final_table

def name_file():
	print('naming file...')
	filename = 'flite_lookup_' + time.strftime("%Y%m%d") + '.csv'
	return filename

#writes data to csv with date at the end of the file
def write_table(final_table,filename):
	print('writing csv...')
	with open(localpath + filename,'w',newline='') as f:
		writer = csv.writer(f)
		writer.writerows(final_table) 


def open_connection():
	print('connecting to acxiom sftp for upload...')
	#make connection
	transport = paramiko.Transport(('esftpi.acxiom.com'))
	transport.connect(username='eaf736', password='8SNx4J9$')
	sftp = paramiko.SFTPClient.from_transport(transport)
	return sftp


#execute everything
final_table = compile_campaigns()
filename = name_file()
write_table(final_table,filename)

##copy from hard drive to axiom's sftp
#sftp = open_connection()
#sftp.put(localpath + filename,filename)
#print ('files on sftp:')
#print (sftp.listdir())

