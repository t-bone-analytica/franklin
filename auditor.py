#!/usr/env python

import requests
from bs4  import BeautifulSoup
from lxml import html


SEARCH_FORM_URL = "http://property.franklincountyauditor.com/_web/search/commonsearch.aspx?mode=parid"

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


    tax_status_table = parsedResults.find('table', {'id': '2017 Tax Status'})
    tax_status_cells = tax_status_table.findAll('td')

    return tax_status_cells[1].contents[0]

