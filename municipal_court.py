#!/usr/env python

import requests
from bs4  import BeautifulSoup
from lxml import html


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
    print( search_csrf_token )

    # Submit search request
    search_form_parameters = {
        '_token': search_csrf_token,
        'case_number': CASE_NUMBER
    }
    results_request = session_requests.post(RESULTS_URL, search_form_parameters)
    parsedResults = BeautifulSoup(results_request.content, 'html.parser')

    # Retreive first result from search
    results_table = parsedResults.find('table', {'id': 'datatable'})
    results_form_inputs = results_table.findAll('input')

    # Submit post to view case details
    view_form_parameters = {
        '_token':  results_form_inputs[0]['value'],
        'case_id': results_form_inputs[1]['value']
    }
    view_request = session_requests.post(VIEW_URL, view_form_parameters)





if __name__ == '__main__':
    main()