#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
#
# This is free and unencumbered software released into the public domain.

import sys, os, time, argparse, configparser
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import FirefoxProfile
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def parse_arguments():
    """Gathers command-line options.

    Returns:
        argparse.Namespace: Arguments parsed using ``argparse``.
    """
    p = argparse.ArgumentParser(
            description="Extracts information about who likes a given Facebook page."
            )
    p.add_argument(
            'oid',
            help="The Facebook Page object's numeric ID or name."
            )
    p.add_argument(
            '--output-format', '-f',
            choices=['csv','json'],
            default='csv',
            help="Format of exported data. Defaults to csv."
            )
    p.add_argument(
            '--profile-path',
            required=True,
            help="Filesystem path to the Firefox profile you want to use. (Default is to use a new, temporary profile.)"
            )
    args = p.parse_args()
    return args

def web_element_to_dict(el):
    """Converts a Selenium WebElement to a standard Python dict.
    
    Args:
        el (WebElement): The WebElement to convert.

    Returns:
        dict
    """
    d = {}
    d['text'] = el.text
    if el.get_attribute('href'):
        d['href'] = el.get_attribute('href')
    return d

def profile_link_to_dict(el):
    """Gets a dictionary representation of a Selenium WebElement of a profile link.

    Args:
        el (WebElement): The WebElement to convert.

    Returns:
        dict
    """
    d = web_element_to_dict(el)
    r = dict(d)
    t = r.pop('text', None) # avoid KeyError
    u = r.pop('href', None).split('?', 1)[0]
    r['Name'] = t
    r['URL'] = u
    return r

def output_csv(profile_list):
    """Writes gathered info in CSV format.

    Args:
        profile_list (List[selenium.webdriver.remote.webelement.WebElement]): The found list of profile link elements.

    Returns:
        None
    """
    import csv
    writer = csv.DictWriter(sys.stdout, fieldnames=['Name', 'URL'])
    writer.writeheader()
    rows = [profile_link_to_dict(el) for el in profile_list]
    for row in rows:
        writer.writerow(row)

def output_json(profile_list):
    """Writes gathered info in JSON format.

    Args:
        profile_list (List[selenium.webdriver.remote.webelement.WebElement]): The found list of profile link elements.

    Returns:
        None
    """
    import json
    rows = [profile_link_to_dict(el) for el in profile_list]
    print(json.dumps(rows, indent=2))

def main():
    # Process CLI args.
    args = parse_arguments()

    # Load the XPaths strings.
    xpaths = configparser.ConfigParser()
    xpaths.read('fb-xpath.ini')

    # Get the Firefox profile to use.
    profile = None
    if args.profile_path:
        profile = FirefoxProfile(args.profile_path)

    # Construct the URLs to load.
    urls = [
        'https://www.facebook.com/{}/settings/?tab=people_and_other_pages'.format(args.oid)
    ]
    # TODO: Determine if these values are different for pages vs. groups vs. profiles, etc.
    #       We are assuming pages for now.
    xpaths = xpaths['Page']

    # Drive!
    driver = webdriver.Firefox(profile)

    for url in urls:
        # Load the page.
        driver.get(url)
        # Click the "See More" link until it's gone.
        while True:
            try:
                wait = WebDriverWait(driver, 10)
                el = wait.until(
                    EC.element_to_be_clickable((By.XPATH, xpaths.get('see_more_link')))
                    )
                driver.execute_script('arguments[0].scrollIntoView()', el)
            except TimeoutException:
                # This will be raised when Facebook removes the element.
                # It means we've reached the end of the "See More" list.
                break

        # Now the whole list of people who like our page is loaded.
        profiles = driver.find_elements_by_xpath(xpaths.get('profile_link'))

    if 'csv' == args.output_format:
        output_csv(profiles)
    elif 'json' == args.output_format:
        output_json(profiles)

    driver.quit()

if __name__ == "__main__":
    main()
