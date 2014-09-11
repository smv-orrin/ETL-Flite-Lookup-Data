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
auth = OAuth1('oyn3xhresbffqqwfbk9zxtx6ibj8l93taniqgkatd4abqw2knftmhzgahgnapxevzsa87dyjxbcwxyfjgstr6xgrnvvf5vqf',
			  'kHPJw5NNKSwKrdGNACqgYKF4Gy6yJCZ4QXW0njFlRCQiWEhBg6ixcDv2WrtnMbP9',
              'oyn3xhresbffqqwfbk9zxtx6ibj8l93taniqgkatd4abqw2knftmhzgahgnapxevzsa87dyjxbcwxyfjgstr6xgrnvvf5vqf', 
              'kHPJw5NNKSwKrdGNACqgYKF4Gy6yJCZ4QXW0njFlRCQiWEhBg6ixcDv2WrtnMbP9')


#define campaigns & their guids
guid_dict = dict([("tidepodsfree", "78fb561d-ab39-462d-a79e-ccb0d2644e96"),
						("tidevariant","a489f4bb-3a61-451e-9a8d-b3567cea516c")])


#define a local path for file mgt prior to sftp upload
localpath = 'C:\\Users\\orrwatso\\Documents\\Data-Sources\\Flite\\'

#requests data from 60 days prior though today
def get_reportID(guid, auth):
	#request data to be processed
	url = "http://api.flite.com/rr/v1.0/data/report/campaign/" + guid + ".csv?"
	
	params = {"start": "07/01/2014", "end": "07/15/2014", "columns": "adName,adId", "names": "creativeMetadata"}
	
	params.update(end = time.strftime("%m/%d/%Y"))
	
	d = date.today() - timedelta(days=60)
	
	params.update(start = d.strftime("%m/%d/%Y"))
	
	#report_guid = requests.get(url,params=params, auth=auth )
	#print report_guid
	
	report_guid = requests.get(url,params=params, auth=auth).json()
	report_guid = report_guid.get('reportId')
	
	return(report_guid)



#get report status
#this returns nothing intiially.  need to wait a few seconds.
def get_status(report_guid, auth):
	info = "http://api.flite.com/rr/v1.0/data/report/info/"
	info = info + report_guid
	info_response = requests.get(info, auth=auth).json()
	#print info_response #this is report request metadata
	status = info_response.get('status')
	return(status)


#waits for flite's api to process the data
def wait_for_processing(report_guid,auth):
	status = []
	#check status every 5 seconds
	start = time.clock()
	now = time.clock()
	while  (str(status) != 'COMPLETE') :
		time.sleep(5)
		try:
			status = get_status(report_guid,auth)
		except:
			print('bad api response')
		print(status, 'for ', now - start, 'seconds')
		now = time.clock()
		if now - start > 300 :
			print('api call timed out')
			break


#returns a csv of duplicated rows
def get_data(report_guid, auth):
	data_url = "http://api.flite.com/rr/v1.0/data/report/download/"
	data_url = data_url + report_guid 
	data_response = requests.get(data_url, auth=auth)

	creativeMetadata = str(data_response.text)
	return creativeMetadata


#cleans & dedups, puts data into a python list
def dedup_clean_data(creativeMetadata):
	data_rows = creativeMetadata.split("\n")

	nice_data = [i.split(',') for i in data_rows]

	deduped = []
	for row in nice_data:
		if row not in deduped and row != ['']:
			deduped.append(row)

	deduped = deduped[1:len(deduped)] #remove headers

	return deduped


#run all functions above
def creative_lookup(guid,auth):

	try:
		report_guid = get_reportID(guid,auth)
	except:
		print('bad api response')

	wait_for_processing(report_guid,auth)

	creativeMetadata = get_data(report_guid,auth)

	data = dedup_clean_data(creativeMetadata)

	return data


#iterate over creative_lookup()
def compile_campaigns(guid_dict):
	final_table = []
	for campaign,guid in guid_dict.items():
		data = creative_lookup(guid,auth)
		for row in data:
			final_table.append(row)
	return final_table

def name_file():
	filename = 'flite_lookup_' + time.strftime("%Y%m%d") + '.csv'
	return filename

#writes data to csv with date at the end of the file
def write_table(final_table,filename):
	with open(localpath + filename,'wt',newline='') as f:
		writer = csv.writer(f)
		#final_table_iter = iter(final_table)
		writer.writerows(final_table) 


def open_connection():
	#make connection
	transport = paramiko.Transport(('esftpi.acxiom.com'))
	transport.connect(username='eaf736', password='8SNx4J9$')
	sftp = paramiko.SFTPClient.from_transport(transport)
	return sftp


#execute everything
final_table = compile_campaigns(guid_dict)

filename = name_file()

write_table(final_table,filename)

#copy from hard drive to axiom's sftp
sftp = open_connection()
sftp.put(localpath + filename,filename)
#
print ('files on sftp:')
print (sftp.listdir())

