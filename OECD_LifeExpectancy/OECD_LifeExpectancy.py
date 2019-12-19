import os
import re
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines
import requests
from bs4 import BeautifulSoup
from matplotlib.ticker import MaxNLocator



def mkdir_p(mypath):
    '''Creates a directory. equivalent to using mkdir -p on the command line

    code from:
    https://stackoverflow.com/questions/11373610/save-matplotlib-file-to-a-directory
    '''

    from errno import EEXIST
    from os import makedirs, path

    try:
        makedirs(mypath)
    except OSError as exc:  # Python >2.5
        if exc.errno == EEXIST and path.isdir(mypath):
            pass
        else:
            raise


def load_life_expectancy_data():
    f_path_name = os.path.join(
        os.getcwd(), 'OECD_LifeExpectancy', 'OECD_LifeExpectancy_data.csv')

    return pd.read_csv(f_path_name)


def get_country_codes(reload_data=False):
    '''
    Returns a dictionary from a csv file saved locally.
    If the csv file is not found, or if the data needs to be
    refreshed, the file is (re)built by scraping it from
    countrycode.org.

    inputs:
    reload_data     bool    whether the data should be scraped
                            from the country code website.

    output:
    a dictionary mapping three-letter (iso) country codes to country names.
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

    # There are two OECD countries for which the countries names in
    # the country code list does not match the OECD members list.
    # KOR -> South Korea -> Korea
    # SVK -> Slovakia -> Slovak Republic
    # There may be non-oecd countries whose name do not match.
    match_names = {'Slovakia': 'Slovak Republic', 'South Korea': 'Korea'}
    cc['Country'] = cc['Country'].replace(match_names)

    return cc.set_index('Code')['Country'].to_dict()


def find_code_by_country(country):
    cc = get_country_codes()
    cc = {cntry: code for code, cntry in cc.items()}

    try:
        return cc[country]
    except KeyError:
        print(f'No country code was found for {country}')
        return None


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


def get_top_countries(year, top=10, oecd_only=True):
    df = load_life_expectancy_data()
    country_names = get_country_codes()

    df['LOCATION'] = df['LOCATION'].replace(country_names)

    if oecd_only:
        oecd_members = get_oecd_members()
        df = df.loc[df['LOCATION'].isin(oecd_members)]

    top_countries = (df.loc[(df['TIME'] == year) & (df['SUBJECT'] == 'TOT')]
                       .sort_values(by='Value', ascending=False)
                       .head(top))['LOCATION']

    df = (df.loc[(df['LOCATION'].isin(top_countries)) & (df['TIME'] == year)]
          [['LOCATION', 'SUBJECT', 'Value']]
          .pivot(index='LOCATION', columns='SUBJECT', values='Value')
          .sort_values(by='TOT'))

    return df.copy()

def insert_title(ax, title, subtitle):
    ax.annotate(title, (0.02,0.98),
                xycoords='figure fraction', fontweight='bold',
                fontsize='large', va='top', ha='left')
    ax.annotate(subtitle, (0.02,0.92),
                 xycoords='figure fraction', fontweight='light',
                 fontsize='small', va='top', ha='left', color='#5F5F5F')


def create_dotplot(year, top=10, oecd_only=True):
    df = get_top_countries(year, top, oecd_only)

    fig, ax = plt.subplots(figsize=(4, 4.75), dpi=140)
    fig.subplots_adjust(bottom=0.0, top=0.81, left=0.25, right=0.96)

    ax.errorbar(df['TOT'],
                df.index,
                xerr=[df['TOT'] - df['MEN'], df['WOMEN'] - df['TOT']],
                ls='', marker='o', ms=6, mfc='#FFFFFF', mec='#4A4A4A', mew=1.5,
                elinewidth=0.5, capsize=3.5, capthick=1.5, ecolor='#4A4A4A')

    set_dotplot_axis_appearance(ax)
    anno_locs = df.loc[df['TOT'].idxmax()][['MEN', 'TOT', 'WOMEN']].to_list()
    label_dotplot_points(ax, anno_locs)

    title = 'Life Expectancy at Birth'
    subtitle = f'Top {top} OECD Countries, {year}'
    insert_title(ax, title, subtitle)

    mkdir_p('Output_Figures')
    f_path = os.path.join(os.getcwd(), 'Output_Figures')
    f_name = f'LifeExpectancy_{year}.png'
    fig.savefig(os.path.join(f_path, f_name), bbox_inchex='auto', pad_inches=0)


def set_dotplot_axis_appearance(ax):
    spine_colour = '#8A8A8A'
    label_colour = '#3D3D3D'

    ax.xaxis.set_ticks_position('top')

    for side in ['left', 'right', 'bottom']:
        ax.spines[side].set_visible(False)
    ax.tick_params(left=False, right=False, bottom=False)

    ax.spines['top'].set_color(spine_colour)
    ax.tick_params(axis='y', colors=label_colour)
    ax.tick_params(axis='x', colors=spine_colour)
    ax.tick_params(axis='x', direction='out', top=True)

    ax.xaxis.label.set_color(label_colour)
    ax.xaxis.set_label_position('top')
    ax.margins(x=0.2, y=0.15)

    xticks = ax.get_xticks()
    ax.spines['top'].set_bounds(xticks[1], xticks[-2])


def label_dotplot_points(ax, anno_loc):
    spine_colour = '#8A8A8A'
    anno_text = ['Men', 'Both', 'Women']

    ln = matplotlib.lines.Line2D([anno_loc[0], anno_loc[-1]], [0.96, 0.96],
                                 color=spine_colour, lw=1,
                                 transform=ax.get_xaxis_transform())
    ax.add_line(ln)

    for txt, xcoord in zip(anno_text, anno_loc):
        ax.annotate(txt, (xcoord, 0.96),
                    xycoords=('data', 'axes fraction'),
                    va='center', ha='center', color=spine_colour,
                    fontsize='small',
                    bbox=dict(boxstyle='square,pad=0.5', fc='#FFFFFF', ec='none'))


def get_country_expectancy_data(country, years):
    '''
    Extract the life expectancy data for a specified country for the years
    provided.
    '''
    df = load_life_expectancy_data()
    country_code = find_code_by_country(country)

    df = (df.loc[(df['LOCATION'] == country_code) & (df['TIME'].isin(years))]
          [['TIME', 'SUBJECT', 'Value']]
          .pivot(index='TIME', columns='SUBJECT', values='Value')
          .sort_index(ascending=True))

    return df.copy()


def plot_country_life_expectancy(country, years):
    exp = get_country_expectancy_data(country, years)

    colours = {'MEN':'#252525', 'WOMEN':'#5F5F5F'}

    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=140)
    fig.subplots_adjust(bottom=0.1, top=0.87, left=0.05, right=0.9)

    subjects = ['MEN', 'WOMEN']
    for subject in subjects:
        ax.plot(exp.index, exp[subject], label=subject,
                color=colours[subject], marker='o',
                mfc='#FFFFFF', mec=colours[subject])
    
    annotate_points(ax, colours)
    set_country_life_expectancy_appearance(ax)

    title = 'Life Expectancy at Birth'
    start, end = exp.index[0], exp.index[-1]
    subtitle = f'By year from {start} to {end}, {country.capitalize()}'
    insert_title(ax, title, subtitle)

    
    mkdir_p('Output_Figures')
    f_path = os.path.join(os.getcwd(), 'Output_Figures')
    f_name = f'LifeExpectancy_{country}_({start}_{end}).png'
    fig.savefig(os.path.join(f_path, f_name), bbox_inchex='auto', pad_inches=0)

def annotate_points(ax, colours):
    for line in ax.get_lines():
        xs, ys = line.get_data()
        label = line.get_label()

        for x,y in zip(xs, ys):
            ax.annotate(f'{y:0.1f}', (x,y),
                        xytext=(0, 10), textcoords='offset points',
                        color=colours[label],
                        va='bottom', ha='center', fontsize='small')

        ax.annotate(label.capitalize(), (xs[-1], ys[-1]),
                    xytext=(15, 0), textcoords='offset points',
                    color=colours[label],
                    va='center', ha='left', fontsize='medium')

def set_country_life_expectancy_appearance(ax):
    spine_colour = '#8A8A8A'

    for side in ['right', 'top']:
        ax.spines[side].set_visible(False)
    ax.tick_params(right=False, top=False)

    for side in ['left', 'bottom']:
        ax.spines[side].set_color(spine_colour)
    ax.tick_params(axis='y', colors=spine_colour)
    ax.tick_params(axis='x', colors=spine_colour)
    # ax.tick_params(axis='x', direction='out', top=True)

    ax.xaxis.label.set_color(spine_colour)
    ax.yaxis.label.set_color(spine_colour)

    xs, ys = [], []
    for line in ax.get_lines():
        line_data = line.get_data()
        xs.append(line_data[0])
        ys.append(line_data[1])
    xs = [val for vals in xs for val in vals]
    ys = [val for vals in ys for val in vals]
    
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    xticks, yticks = ax.get_xticks(), ax.get_yticks()
    ax.spines['bottom'].set_bounds(xticks[1], xticks[-2])
    ax.spines['left'].set_bounds(yticks[1], yticks[-2])


if __name__ == '__main__':
    create_dotplot(2010)
    plot_country_life_expectancy('Canada', list(range(1960, 2018,5)))
    plot_country_life_expectancy('France', list(range(1960, 2018,5)))