#!/usr/env python

import os
import time
import requests
import mysql.connector
from bs4  import BeautifulSoup
from lxml import html
from dotenv import load_dotenv

import traceback
from pprint import pprint

load_dotenv()

RUNNING = 1
CURRENT_RECORD = "not set yet"
SEARCH_FORM_URL = "http://property.franklincountyauditor.com/_web/search/commonsearch.aspx?mode=parid"
TAX_URL = "http://property.franklincountyauditor.com/_web/datalets/datalet.aspx?mode=taxpayments&sIndex=7&idx=1&LMparent=20"

def main():
    global CURRENT_RECORD
    global RUNNING

    SCRAPE_COUNT = 0
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
                "ts_tax_district"        : get_ts_tax_district(summary_soup),
                "ts_school_district"     : get_ts_school_district(summary_soup),
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
                "net_annual_tax"         : get_net_annual_tax(tax_soup),
                "tyd_annual_total"       : get_tyd_annual_total(tax_soup),
                "tyd_payment_total"      : get_tyd_payment_total(tax_soup),
                "tyd_total_total"        : get_tyd_total_total(tax_soup)
            }
            store_data(data)
            SCRAPE_COUNT += 1
        except:
            store_error()
        # Dodge the rate limit for requests
        time.sleep(2)

        RUNNING = get_next_record()
    if SCRAPE_COUNT > 0:
        os.system("php " + os.getenv("ARTISAN_PATH") + " export:tax-info")




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
    cursor.execute("SELECT `parcel_id` FROM `tax_info` WHERE `status` = 0 ORDER BY `id` ASC LIMIT 1")
    result = cursor.fetchone()
    if cursor.rowcount is 1:
        CURRENT_RECORD = str( result[0] )
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
    sql = """
        UPDATE `tax_info`
        SET
            `status` = 1,
            `address` = %s,
            `ts_zip_code` = %s,
            `company_name` = %s,
            `tbm_name_1` = %s,
            `tbm_name_2` = %s,
            `tbm_address` = %s,
            `tbm_city_state_zip` = %s,
            `ts_tax_district` = %s,
            `ts_school_district` = %s,
            `ts_rental_registration` = %s,
            `ts_tax_lien` = %s,
            `dd_year_built` = %s,
            `dd_fin_area` = %s,
            `dd_bedrooms` = %s,
            `dd_full_baths` = %s,
            `dd_half_baths` = %s,
            `sd_acres` = %s,
            `mrt_tansfer_date` = %s,
            `mrt_transfer_price` = %s,
            `property_class` = %s,
            `land_use` = %s,
            `net_annual_tax` = %s,
            `tyd_annual_total` = %s,
            `tyd_payment_total` = %s,
            `tyd_total_total` = %s
        WHERE
            (`parcel_id` = %s);
    """
    values = (
                str( data["address"] ),
                str( data["ts_zip_code"] ),
                str( data["company_name"] ),
                str( data["tbm_name_1"] ),
                str( data["tbm_name_2"] ),
                str( data["tbm_address"] ),
                str( data["tbm_city_state_zip"] ),
                str( data["ts_tax_district"] ),
                str( data["ts_school_district"] ),
                str( data["ts_rental_registration"] ),
                str( data["ts_tax_lien"] ),
                str( data["dd_year_built"] ),
                str( data["dd_fin_area"] ),
                str( data["dd_bedrooms"] ),
                str( data["dd_full_baths"] ),
                str( data["dd_half_baths"] ),
                str( data["sd_acres"] ),
                str( data["mrt_tansfer_date"] ),
                str( data["mrt_transfer_price"] ),
                str( data["property_class"] ),
                str( data["land_use"] ),
                str( data["net_annual_tax"] ),
                str( data["tyd_annual_total"] ),
                str( data["tyd_payment_total"] ),
                str( data["tyd_total_total"] ),
                str(CURRENT_RECORD)
    )

    cursor.execute(sql, values)
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
    cursor.execute(sql)
    db.commit()




def get_status(soup):
    return 'NULL'



def get_parcel_id(soup):
    return CURRENT_RECORD



def get_address(soup):
    return soup.find('tr', {'id': 'datalet_header_row'}).findChildren('td', {'class': 'DataletHeaderBottom'})[1].contents[0]



def get_ts_zip_code(soup):
    return soup.find('table', {'id': '2017 Tax Status'}).findChildren('td', {'class': 'DataletData'})[13].contents[0]



def get_company_name(soup):
    return ''



def get_tbm_name_1(soup):
    name = soup.find('table', {'id': 'Owner'}).findChildren('td', {'class': 'DataletData'})[11].contents[0]
    return name.replace(u'\xa0', '')



def get_tbm_name_2(soup):
    name = soup.find('table', {'id': 'Owner'}).findChildren('td', {'class': 'DataletData'})[12].contents[0]
    return name.replace(u'\xa0', '')



def get_tbm_address(soup):
    return soup.find('table', {'id': 'Owner'}).findChildren('td', {'class': 'DataletData'})[13].contents[0]



def get_tbm_city_state_zip(soup):
    return soup.find('table', {'id': 'Owner'}).findChildren('td', {'class': 'DataletData'})[14].contents[0]



def get_ts_tax_district(soup):
    return soup.find('table', {'id': '2017 Tax Status'}).findChildren('td', {'class': 'DataletData'})[2].contents[0]



def get_ts_school_district(soup):
    return soup.find('table', {'id': '2017 Tax Status'}).findChildren('td', {'class': 'DataletData'})[3].contents[0]



def get_ts_rental_registration(soup):
    return soup.find('table', {'id': '2017 Tax Status'}).findChildren('td', {'class': 'DataletData'})[11].contents[0]



def get_ts_tax_lien(soup):
    return soup.find('table', {'id': '2017 Tax Status'}).findChildren('td', {'class': 'DataletData'})[7].contents[0]



def get_dd_year_built(soup):
    if soup.find('table', {'id': 'Dwelling Data'}):
        return soup.find('table', {'id': 'Dwelling Data'}).findChildren('td', {'class': 'DataletData'})[0].contents[0]
    else:
        return ''



def get_dd_fin_area(soup):
    if soup.find('table', {'id': 'Dwelling Data'}):
        return soup.find('table', {'id': 'Dwelling Data'}).findChildren('td', {'class': 'DataletData'})[1].contents[0]
    else:
        return ''



def get_dd_bedrooms(soup):
    if soup.find('table', {'id': 'Dwelling Data'}):
        return soup.find('table', {'id': 'Dwelling Data'}).findChildren('td', {'class': 'DataletData'})[3].contents[0]
    else:
        return ''



def get_dd_full_baths(soup):
    if soup.find('table', {'id': 'Dwelling Data'}):
        return soup.find('table', {'id': 'Dwelling Data'}).findChildren('td', {'class': 'DataletData'})[4].contents[0]
    else:
        return ''



def get_dd_half_baths(soup):
    if soup.find('table', {'id': 'Dwelling Data'}):
        return soup.find('table', {'id': 'Dwelling Data'}).findChildren('td', {'class': 'DataletData'})[4].contents[0]
    else:
        return ''



def get_sd_acres(soup):
    try:
        return soup.find('table', {'id': 'Site Data'}).findChildren('td', {'class': 'DataletData'})[2].contents[0]
    except:
        try:
            return soup.find('table', {'id': 'Site Data'}).findChildren('td', {'class': 'DataletData'})[6].contents[0]
        except:
            return ''



def get_mrt_tansfer_date(soup):
    return soup.find('table', {'id': 'Most Recent Transfer'}).findChildren('td', {'class': 'DataletData'})[0].contents[0]



def get_mrt_transfer_price(soup):
    return soup.find('table', {'id': 'Most Recent Transfer'}).findChildren('td', {'class': 'DataletData'})[1].contents[0]



def get_property_class(soup):
    return soup.find('table', {'id': 'Tax Status'}).findChildren('td', {'class': 'DataletData'})[0].contents[0]



def get_land_use(soup):
    return soup.find('table', {'id': 'Tax Status'}).findChildren('td', {'class': 'DataletData'})[1].contents[0]



def get_net_annual_tax(soup):
    return soup.find('table', {'id': 'Tax Status'}).findChildren('td', {'class': 'DataletData'})[3].contents[0]



def get_tyd_annual_total(soup):
    return soup.find('table', {'id': 'Tax Year Detail'}).findChildren('td', {'class': 'DataletData'})[61].contents[0]



def get_tyd_payment_total(soup):
    return soup.find('table', {'id': 'Tax Year Detail'}).findChildren('td', {'class': 'DataletData'})[63].contents[0]



def get_tyd_total_total(soup):
    return soup.find('table', {'id': 'Tax Year Detail'}).findChildren('td', {'class': 'DataletData'})[64].contents[0]





if __name__ == '__main__':
    main()
