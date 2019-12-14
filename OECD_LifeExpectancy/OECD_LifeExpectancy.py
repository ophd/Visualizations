import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup


def load_data():
    ''' Load the OECD life expectancy data from file '''
    f_path_name = os.path.join(
        os.getcwd(), 'OECD_LifeExpenctancy', 'OECD_LifeExpectancy_data.csv')

    return pd.read_csv(f_path_name)


def dotplot(df):
    pass


def get_country_codes(reload_data=False):
    '''
    Returns a Pandas DataFrame from a csv file saved locally.
    If the csv file is not found, or if the data needs to be
    refreshed, the file is (re)built by scraping it from
    countrycode.org.

    inputs:
    reload_data     bool    whether the data should be scraped
                            from the country code website.

    output:
    a DataFrame containing the country codes.
    '''
    f_path_name = os.path.join(
        os.getcwd(), 'OECD_LifeExpectancy', 'country_codes.csv')
    if not os.path.isfile(f_path_name):
        reload_data = True

    # Scrape the country code information from the listed website
    if reload_data:
        url = 'https://www.countrycode.org/'

        r = requests.get(url)
        # headers={'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'})

        soup = BeautifulSoup(r.text, 'html.parser')
        countries = soup.find('table', {'class': 'main-table'})

        with open(f_path_name, 'w') as f:
            # Extract table header
            header = []
            for th in countries.thead.find_all('th'):
                header.append(th.attrs['data-field'])
            f.write(','.join(header))
            f.write('\n')
            del header

            # Extract data
            for tr in countries.tbody.find_all('tr'):
                # Some values in the table have number with comma-separated thousands.
                # Must remove the commas to avoid problems with improperly formatted csv file
                f.write(','.join([td.text.strip().replace(',', '')
                                  for td in tr.find_all('td')]))
                f.write('\n')

    cc = pd.read_csv(f_path_name)
    cc = cc.rename(columns={'name': 'Country', 'iso': 'Code'})
    cc['Code'] = cc['Code'].str.replace(r'.*/.?(\w{3})', '\\1', regex=True)

    return cc[['Country', 'Code']]


def get_oecd_members(reload_data=False):
    '''
    Returns a list of countries from a csv file saved locally.
    If the csv file is not found, or if the data needs to be
    refreshed, the file is (re)built by scraping it from the
    OECD website.

    inputs:
    reload_data     bool    whether the data should be scraped
                            from the country code website.

    output:
    a list of OECD members.
    '''
    f_path_name = os.path.join(
        os.getcwd(), 'OECD_LifeExpectancy', 'oecd_members.csv')

    if not os.path.isfile(f_path_name):
        reload_data = True

    if reload_data:
        url = 'https://www.oecd.org/about/members-and-partners/'

        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        # There are several lists with class 'country-list__box'. The one
        # containing current OECD members is the first list on the page.
        members = (soup.find_all('div', {'class': 'country-list__box'})[0]
                       .find_all('a', {'class': 'country-list__country'}))

        members = [member.text.strip() for member in members]

        with open(f_path_name, 'w') as f:
            for member in members:
                f.write(f'{member}\n')
    else:
        with open(f_path_name, 'r') as f:
            members = f.read().split('\n')

    return members


if __name__ == '__main__':
    codes = get_country_codes()
    members = get_oecd_members()

    print(codes)
    print('\n\n-----------------\n\n')
    print(members)
    # df = load_data()

    # TODO: use get_country_codes() when loading life expectancy data to replace values in country columns
    # TODO: use get_oecd_members() to filter out OECD members when loading data.
    # TODO: get top 10 countries from OECD in 2010 data and produce dotplot sim. to Dark Horse analytics

    # # Get list of top ten countries for 2010 by total life expectancy at birth
    # top10 = (df.loc[(df['TIME'] == 2010) & (df['SUBJECT'] == 'TOT')]
    #           .sort_values(by='Value', ascending=False)
    #           .iloc[:10]['LOCATION'])
