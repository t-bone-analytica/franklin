#!/usr/env python

import os
import time
import requests
import mysql.connector
from bs4  import BeautifulSoup
from lxml import html
from dotenv import load_dotenv

from pprint import pprint

load_dotenv()

RUNNING = 1
CURRENT_RECORD = "not set yet"
SEARCH_FORM_URL = "http://property.franklincountyauditor.com/_web/search/commonsearch.aspx?mode=parid"
TAX_URL = "http://property.franklincountyauditor.com/_web/datalets/datalet.aspx?mode=taxdistribution&sIndex=0&idx=1&LMparent=20"

def main():
    global CURRENT_RECORD
    global RUNNING

    RUNNING = get_next_record()
    while RUNNING is 1:
        try:
            # Create a persistent session
            session_requests = requests.session()
            summary_soup = get_summary(session_requests)
            tax_soup = get_tax_info(session_requests)
            data = {
                "parcel_id"              : get_parcel_id(summary_soup),
                "address"                : get_address(summary_soup),
                "ts_zip_code"            : get_ts_zip_code(summary_soup),
                "company_name"           : get_company_name(summary_soup),
                "tbm_name_1"             : get_tbm_name_1(summary_soup),
                "tbm_name_2"             : get_tbm_name_2(summary_soup),
                "tbm_address"            : get_tbm_address(summary_soup),
                "tbm_city_state_zip"     : get_tbm_city_state_zip(summary_soup),
                "ts_address_1"           : get_ts_address_1(summary_soup),
                "ts_address_2"           : get_ts_address_2(summary_soup),
                "ts_rental_registration" : get_ts_rental_registration(summary_soup),
                "ts_tax_lien"            : get_ts_tax_lien(summary_soup),
                "dd_year_built"          : get_dd_year_built(summary_soup),
                "dd_fin_area"            : get_dd_fin_area(summary_soup),
                "dd_bedrooms"            : get_dd_bedrooms(summary_soup),
                "dd_full_baths"          : get_dd_full_baths(summary_soup),
                "dd_half_baths"          : get_dd_half_baths(summary_soup),
                "sd_acres"               : get_sd_acres(summary_soup),
                "mrt_tansfer_date"       : get_mrt_tansfer_date(summary_soup),
                "mrt_transfer_price"     : get_mrt_transfer_price(summary_soup),
                "property_class"         : get_property_class(tax_soup),
                "land_use"               : get_land_use(tax_soup),
                "net_annual_tax"         : get_net_annual_tax(tax_soup)
            }
            store_data(data)
        except:
            store_error()
        # Dodge the rate limit for requests
        time.sleep(2)

        RUNNING = get_next_record()
    print('END')




def get_next_record():
    global CURRENT_RECORD

    # Initialize database connection
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        passwd=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
    cursor = db.cursor()
    # Get the next property id to be classified
    cursor.execute("SELECT `parcel_id` FROM `tax_info` WHERE `status` = 99 ORDER BY `id` ASC LIMIT 1")
    result = cursor.fetchone()
    if cursor.rowcount is 1:
        CURRENT_RECORD = str( result[0] )
        print("got next record: " + CURRENT_RECORD)
        return 1
    else:
        print("Could not find any more records")
        return 0



def get_summary(session_requests):
    global CURRENT_RECORD

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
        "inpParid"           : CURRENT_RECORD
    }
    results_request = session_requests.post(SEARCH_FORM_URL, search_form_parameters)
    return BeautifulSoup(results_request.content, 'html.parser')



def get_tax_info(session_requests):
    global CURRENT_RECORD

    tax_request = session_requests.get(TAX_URL)
    # file = open("tax.html", "w")
    # file.write(tax_request.text)
    # file.close()
    return BeautifulSoup(tax_request.content, 'html.parser')




def store_data(data):
    global CURRENT_RECORD
    # Initialize database connection
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        passwd=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
    cursor = db.cursor()
    print("Storing scraped data")
    sql = "UPDATE `tax_info` SET `status` = 1 WHERE `parcel_id` = '" + str(CURRENT_RECORD) + "' LIMIT 1"
    val = ( CURRENT_RECORD )
    cursor.execute(sql)
    db.commit()



def store_error():
    global CURRENT_RECORD
    # Initialize database connection
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        passwd=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
    cursor = db.cursor()
    print("setting status to -1")
    sql = "UPDATE `tax_info` SET `status` = -1 WHERE `parcel_id` = '" + str(CURRENT_RECORD) + "' LIMIT 1"
    # val = ( CURRENT_RECORD )
    # pprint(sql)
    # pprint(val)
    cursor.execute(sql)
    db.commit()




def get_status(soup):
    return 'NULL'



def get_parcel_id(soup):
    return 'NULL'



def get_address(soup):
    return 'NULL'



def get_ts_zip_code(soup):
    return 'NULL'



def get_company_name(soup):
    return 'NULL'



def get_tbm_name_1(soup):
    return 'NULL'



def get_tbm_name_2(soup):
    return 'NULL'



def get_tbm_address(soup):
    return 'NULL'



def get_tbm_city_state_zip(soup):
    return 'NULL'



def get_ts_address_1(soup):
    return 'NULL'



def get_ts_address_2(soup):
    return 'NULL'



def get_ts_rental_registration(soup):
    return 'NULL'



def get_ts_tax_lien(soup):
    return 'NULL'



def get_dd_year_built(soup):
    return 'NULL'



def get_dd_fin_area(soup):
    return 'NULL'



def get_dd_bedrooms(soup):
    return 'NULL'



def get_dd_full_baths(soup):
    return 'NULL'



def get_dd_half_baths(soup):
    return 'NULL'



def get_sd_acres(soup):
    return 'NULL'



def get_mrt_tansfer_date(soup):
    return 'NULL'



def get_mrt_transfer_price(soup):
    return 'NULL'



def get_property_class(soup):
    return 'NULL'



def get_land_use(soup):
    return 'NULL'



def get_net_annual_tax(soup):
    return 'NULL'






if __name__ == '__main__':
    main()
