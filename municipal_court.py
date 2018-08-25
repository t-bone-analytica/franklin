#!/usr/env python
from pprint import pprint
import os
import sys
import math
import time
import requests
import datetime
import mysql.connector
from bs4  import BeautifulSoup
from lxml import html
from dotenv import load_dotenv

load_dotenv()



CASE_NUMBER = ''

SEARCH_URL    = "http://www.fcmcclerk.com/case/search"
RESULTS_URL = "http://www.fcmcclerk.com/case/search/results"
VIEW_URL    = "http://www.fcmcclerk.com/case/view"

def main():
    # Create a persistent session
    session_requests = requests.session()

    # Retrieve the search form
    search_form_request = session_requests.get(SEARCH_URL)
    parsedForm = BeautifulSoup(search_form_request.content, 'html.parser')

    # Parse out the CSRF token for the search form
    search_csrf_token = parsedForm.find("input", {"name":"_token"})['value']

    # Submit search request
    search_form_parameters = {
        '_token': search_csrf_token,
        'case_number': CASE_NUMBER
    }
    results_request = session_requests.post(RESULTS_URL, search_form_parameters)
    parsedResults = BeautifulSoup(results_request.content, 'html.parser')

    # Retreive first result from search
    results_table = parsedResults.find('table', {'id': 'datatable'})
    try:
        results_form_inputs = results_table.findAll('input')
    except:
        store_failure(CASE_NUMBER)
        return

    # Submit post to view case details
    view_form_parameters = {
        '_token':  results_form_inputs[0]['value'],
        'case_id': results_form_inputs[1]['value']
    }
    view_request = session_requests.post(VIEW_URL, view_form_parameters)
    view_results = BeautifulSoup(view_request.content, 'html.parser')

    # Retreive and store the case overview
    details_overview = view_results.find('a', {'id': 'overview'}).parent
    store_case(CASE_NUMBER, details_overview)

    # Retreive and store the case overview
    details_parties = view_results.find('a', {'id': 'parties'}).parent
    store_parties(CASE_NUMBER, details_parties)








def store_case(CASE_NUMBER, details_overview):
    # Get the cell containing overview information
    table_cells = details_overview.findAll('td')
    overview_contents = table_cells[1].contents

    # Get the case status
    case_status =  overview_contents[3].string.lstrip().replace('Status: ', '')
    if(case_status == 'CLOSED'):
        CASE_STATUS = 1
    else:
        CASE_STATUS = 0

    # Get the case filing date
    date_filed =  overview_contents[6].string.lstrip().replace('Filed: ', '')
    date_filed_parts = date_filed.split('/')
    DATE_FILED = datetime.date(
        int(date_filed_parts[2]),
        int(date_filed_parts[0]),
        int(date_filed_parts[1])
    )

    # Initialize database connection
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        passwd=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

    # Prepare insert query
    mycursor = db.cursor()
    sql = "INSERT INTO `case` (case_number, valid, status, date_filed) VALUES (%s, %s, %s, %s)"
    val = (CASE_NUMBER, '1', CASE_STATUS, DATE_FILED)

    # Insert new data to the case table
    mycursor.execute(sql, val)
    db.commit()
    print("SUCCESS WITH " + CASE_NUMBER)


def store_parties(CASE_NUMBER, details_parties):
    # Initialize database connection
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        passwd=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

    party_info_rows = details_parties.findAll('tr')
    parties_count = math.ceil( (len(party_info_rows) / 4) )
    print( "THERE ARE " + str(parties_count) + " PARTIES")

    data_cells = details_parties.findAll('td', {'class': 'data'})
    for i in range(parties_count):
        PARTY_NAME  = str( data_cells[ (i * 6) + 1].contents[0] )
        PARTY_TYPE  = str( data_cells[ (i * 6) + 2].contents[0] )
        PARTY_ADDR  = str( data_cells[ (i * 6) + 3].contents[0] )
        PARTY_CITY  = str( data_cells[ (i * 6) + 4].contents[0] )
        city_and_zip = data_cells[ (i * 6) + 5].contents
        PARTY_STATE = city_and_zip[0].split("/")[0]
        PARTY_ZIP   = city_and_zip[0].split("/")[1]

        if(PARTY_TYPE == "PLAINTIFF"):
            # Prepare insert query
            mycursor = db.cursor()
            sql = "INSERT INTO `party` (case_number, name, address, city, state, zip) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (CASE_NUMBER, PARTY_NAME, PARTY_ADDR, PARTY_CITY, PARTY_STATE, PARTY_ZIP)

            # Insert new data to the case table
            mycursor.execute(sql, val)
            db.commit()



def store_failure(CASE_NUMBER):
    # Initialize database connection
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        passwd=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

    # Prepare insert query
    mycursor = db.cursor()
    sql = "INSERT INTO `case` (case_number, valid) VALUES (%s, %s)"
    val = (CASE_NUMBER, '0')

    # Insert new data to the case table
    mycursor.execute(sql, val)
    db.commit()
    print( 'I GIVE UP ON ' + CASE_NUMBER )


if __name__ == '__main__':
    main()