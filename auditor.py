#!/usr/env python

import os
import time
import requests
import mysql.connector
from bs4  import BeautifulSoup
from lxml import html
from dotenv import load_dotenv

load_dotenv()


SEARCH_FORM_URL = "http://property.franklincountyauditor.com/_web/search/commonsearch.aspx?mode=parid"


def main():
    status = 'OK'
    while status == 'OK':
        status = select_property_id()
        time.sleep(2)


def select_property_id():
    # Initialize database connection
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        passwd=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
    cursor = db.cursor()

    # Get the next property id to be classified
    cursor.execute("SELECT `parcel_id` FROM `delinquency` WHERE `property_class` is NULL ORDER BY `id` ASC LIMIT 1")
    result = cursor.fetchone()
    try:
        PROPERTY_ID = result[0]
    except:
        return 'ERROR'


    PARCEL_CLASS_STRING = get_property_class(PROPERTY_ID)

    if PARCEL_CLASS_STRING is 0:
        PARCEL_CLASS = 0
    else:
        classes = {
            'R - Residential' : 1,
            'C - Commercial'  : 2,
            'E - Exempt'      : 3,
            'I - Industrial'  : 4,
            'A - Agricultural': 5
        }
        PARCEL_CLASS = classes[PARCEL_CLASS_STRING]

    store_property_class( PROPERTY_ID, PARCEL_CLASS )
    time.sleep(3)
    return 'OK'



def get_property_class(PARCEL_ID):
    # Create a persistent session
    session_requests = requests.session()

    # Retrieve the search form
    search_form_request = session_requests.get(SEARCH_FORM_URL)
    parsedForm = BeautifulSoup(search_form_request.content, 'html.parser')

    # Parse out the required fields for the search form
    PARAM_SCRIPTMANAGER = parsedForm.find("input", {"name": "ScriptManager1_TSM"})['value']
    PARAM_VIEWSTATE     = parsedForm.find("input", {"name": "__VIEWSTATE"})['value']

    # Submit search request
    search_form_parameters = {
        "ScriptManager1_TSM" : PARAM_SCRIPTMANAGER,
        "__VIEWSTATE"        : PARAM_VIEWSTATE,
        "inpParid"           : PARCEL_ID
    }
    results_request = session_requests.post(SEARCH_FORM_URL, search_form_parameters)
    parsedResults = BeautifulSoup(results_request.content, 'html.parser')

    try:
        tax_status_table = parsedResults.find('table', {'id': '2017 Tax Status'})
        tax_status_cells = tax_status_table.findAll('td')
    except:
        return 0

    return tax_status_cells[1].contents[0]


def store_property_class(PROPERTY_ID, PARCEL_CLASS):
    # Initialize database connection
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        passwd=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
    cursor = db.cursor()

    sql = "UPDATE `delinquency` SET `property_class` = %s WHERE `parcel_id` = %s LIMIT 1"
    val = ( str(PARCEL_CLASS), str(PROPERTY_ID) )

    cursor.execute(sql, val)
    db.commit()




if __name__ == '__main__':
    main()
