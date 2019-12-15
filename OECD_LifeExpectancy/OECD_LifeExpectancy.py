import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup


def load_life_expectancy_data():
    f_path_name = os.path.join(os.getcwd(), 'OECD_LifeExpectancy', 'OECD_LifeExpectancy_data.csv')

    return pd.read_csv(f_path_name)

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

def get_top_countries(year, top=10):
    df = load_life_expectancy_data()

    top_countries = (df.loc[(df['TIME']==year) & (df['SUBJECT']=='TOT')]
                       .sort_values(by='Value', ascending=False)
                       .head(top))['LOCATION']

    df = (df.loc[(df['LOCATION'].isin(top_countries)) & (df['TIME']==year)]
            [['LOCATION', 'SUBJECT', 'Value']]
            .pivot(index='LOCATION', columns='SUBJECT', values='Value')
            .sort_values(by='TOT'))

    return df.copy()

def create_dotplot(df, year):
    fig, ax = plt.subplots(figsize=(4,5), dpi=140)
    fig.subplots_adjust(bottom=0.05, top=0.95, left=0.2, right=0.98)

    ax.errorbar(df['TOT'],
                df.index,
                xerr=[df['TOT'] - df['MEN'], df['WOMEN'] - df['TOT']],
                ls='', marker='o', ms=6, mfc='#FFFFFF', mec='#4A4A4A', mew=1.5,
                elinewidth=0.5, capsize=3.5, capthick=1.5, ecolor='#4A4A4A')
    
    set_axis_appearance(ax)

    f_path_name = os.path.join(os.getcwd(),'OECD_LifeExpectancy' ,f'LifeExpectancy_{year}.png')
    fig.savefig(f_path_name, bbox_inchex = 'auto', pad_inches=0)

def set_axis_appearance(ax):
    SPINE_COLOUR = '#C4C4C4'
    LABEL_COLOUR = '#3D3D3D'

    ax.xaxis.set_ticks_position('top')

    for side in ['left','right', 'bottom']:
        ax.spines[side].set_visible(False)
    ax.tick_params(left=False, right=False, bottom=False)

    ax.spines['top'].set_color(SPINE_COLOUR)
    ax.tick_params(axis='y', colors=LABEL_COLOUR)
    ax.tick_params(axis='x', colors=SPINE_COLOUR)
    ax.tick_params(axis='x', direction='out', top=True)

    ax.xaxis.label.set_color(LABEL_COLOUR)
    ax.xaxis.set_label_position('top')
    ax.margins(y=0.05)

if __name__ == '__main__':
    # codes = get_country_codes()
    # members = get_oecd_members()
    le = get_top_countries(2010)
    create_dotplot(le, 2010)
    



    # TODO: use get_country_codes() when loading life expectancy data to replace values in country columns
    # TODO: use get_oecd_members() to filter out OECD members when loading data.
    # TODO: get top 10 countries from OECD in 2010 data and produce dotplot sim. to Dark Horse analytics
    # TODO: Check if country names match in all data sets. e.g., Slovak Republic vs. Slovakia

    # # Get list of top ten countries for 2010 by total life expectancy at birth
    # top10 = (df.loc[(df['TIME'] == 2010) & (df['SUBJECT'] == 'TOT')]
    #           .sort_values(by='Value', ascending=False)
    #           .iloc[:10]['LOCATION'])







'''






def dotplot_pole_age(df):
    print('Creating dot plot for pole age...')
    import matplotlib.transforms as transforms
    fig_path = os.path.join(os.getcwd(), 'results', 'figures')

    ages = (df.pivot_table(values='Pole Age', columns=['Dataset', 'Dataset Year'], 
                  index='Class', aggfunc=[np.mean, np.std])
                .drop([40,50])
                .sort_index(ascending=False))
    ages.index = ages.index.map(lambda x: f'Class {x}')
    # Create a plot for each dataset
    names = ages.columns.get_level_values(1).unique()
    fig, axes = plt.subplots(ncols=len(names), figsize=(7,4.25), dpi=140, sharey=True)
    # Adjust plot spacing
    fig.subplots_adjust(bottom=0.07, top=0.8, left=0.1, right=0.96, wspace=0.05)

    for i, name in enumerate(names):
        # Get all dataset years
        years = ages['mean'][name].columns.get_level_values(0).unique()
        # Used to offset the dataset years
        offset = lambda x,y: transforms.ScaledTranslation(x, y/72., fig.dpi_scale_trans)
        trans = axes[i].transData
        # plot both years with error bars
        # earlier year
        axes[i].errorbar(ages['mean'][name][years[0]], ages.index,
                    xerr=ages['std'][name][years[0]],
                    transform=trans+offset(0,5),
                    ls='', marker=MARKER_STYLES[0], mfc='#FFFFFF', mec=MARKER_COLOURS[0] ,
                    ecolor=ERR_COLOURS[0], elinewidth=ERR_LW, capsize=ERR_CAPSIZE,
                    label=years[0])
        # latest year
        axes[i].errorbar(ages['mean'][name][years[1]], ages.index,
                    xerr=ages['std'][name][years[1]],
                    transform=trans+offset(0,-5),
                    ls='', marker=MARKER_STYLES[1], mfc='#FFFFFF', mec=MARKER_COLOURS[1],
                    ecolor=ERR_COLOURS[1], elinewidth=ERR_LW, capsize=ERR_CAPSIZE,
                    label=years[1])
        
        # Add title
        axes[i].set_title(name, y=1.15, color=LABEL_COLOUR)
        # Set x-axis label
        axes[i].set_xlabel('Pole age (years)')
        # Fix the min and max values of the x-axis
        axes[i].set_xticks(range(10,80,10))
        axes[i].set_xticklabels([f'{x}' if x % 20 == 0 else '' for x in range(10,80,10)])
        # Fix appearance of labels and axes
        set_dotplot_appearance(axes[i])

    fig.savefig(os.path.join(fig_path, f'dotplot_Age_Combined.png'),
            bbox_inchex = 'auto', pad_inches=0)
    # Close figures to remove them from memory
    plt.close(fig)
    print('\tDone.')

def dotplot_pole_age_treatment(df):
    print('Creating dot plot for pole age...')
    import matplotlib.transforms as transforms
    fig_path = os.path.join(os.getcwd(), 'results', 'figures')

    df_treat = (df.pivot_table(values='Pole Age', columns=['Dataset', 'Dataset Year'], 
                  index='Treatment Type', aggfunc=[np.mean, np.std])
                .sort_values(('mean','Coronation',2006), ascending=False))
    # Create a plot for each dataset
    names = df_treat.columns.get_level_values(1).unique()
    fig, axes = plt.subplots(ncols=len(names), figsize=(7,4.25), dpi=140, sharey=True)
    # Adjust plot spacing
    fig.subplots_adjust(bottom=0.07, top=0.8, left=0.1, right=0.96, wspace=0.05)

    for i, name in enumerate(names):
        # Get all dataset years
        years = df_treat['mean'][name].columns.get_level_values(0).unique()
        # Used to offset the dataset years
        offset = lambda x,y: transforms.ScaledTranslation(x, y/72., fig.dpi_scale_trans)
        trans = axes[i].transData
        # plot both years with error bars
        # earlier year
        axes[i].errorbar(df_treat['mean'][name][years[0]], df_treat.index,
                    xerr=df_treat['std'][name][years[0]],
                    transform=trans+offset(0,5),
                    ls='', marker=MARKER_STYLES[0], mfc='#FFFFFF', mec=MARKER_COLOURS[0] ,
                    ecolor=ERR_COLOURS[0], elinewidth=ERR_LW, capsize=ERR_CAPSIZE,
                    label=years[0])
        # latest year
        axes[i].errorbar(df_treat['mean'][name][years[1]], df_treat.index,
                    xerr=df_treat['std'][name][years[1]],
                    transform=trans+offset(0,-5),
                    ls='', marker=MARKER_STYLES[1], mfc='#FFFFFF', mec=MARKER_COLOURS[1],
                    ecolor=ERR_COLOURS[1], elinewidth=ERR_LW, capsize=ERR_CAPSIZE,
                    label=years[1])
        
        # Add title
        axes[i].set_title(name, y=1.15, color=LABEL_COLOUR)
        # Set x-axis label
        axes[i].set_xlabel('Pole age (years)')
        # Fix the min and max values of the x-axis
        axes[i].set_xticks(range(10,80,10))
        axes[i].set_xticklabels([f'{x}' if x % 20 == 0 else '' for x in range(10,80,10)])
        set_dotplot_appearance(axes[i])
        
    fig.savefig(os.path.join(fig_path, f'dotplot_Treatments.png'),
            bbox_inchex = 'auto', pad_inches=0)
    # Close figures to remove them from memory
    plt.close(fig)
    print('\tDone.')

def set_dotplot_appearance(ax):

     # Modify appearance of plot
    # Set ticks to top the top of the figure
    ax.xaxis.set_ticks_position('top')
    # Remove spines on sides
    for side in ['left','right']:
        ax.spines[side].set_visible(False)
    # Change the colour of the x-axis/top & bottom spines
    for side in ['bottom','top']:
        ax.spines[side].set_color(SPINE_COLOUR)
    # Set colour of tick labels
    ax.tick_params(axis='both', colors=SPINE_COLOUR)
    # Set colour of axis labels
    ax.xaxis.label.set_color(LABEL_COLOUR)
    # Remove ticks everywhere except top
    # Move x-axis label to top
    ax.tick_params(left=False, right=False)
    ax.tick_params(axis='x', direction='in', bottom=True, top=True)
    ax.xaxis.set_label_position('top')
    ax.margins(y=0.1)
    # Add gridlines
    ax.grid(b=True, which='both',axis='x', color=GRID_COLOUR, ls=':')
    # Move legend to bottom
    ax.legend(loc='lower center',markerscale = 1,
              bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)
    
def set_axes_appearance(ax, fig, legend_bbox=(0.15, 0.94), ncols=1):

    PLOT_LEGEND_MARKERSCALE = 1.5
    PLOT_GRID_COLOUR = '#DCDCDC'
    PLOT_AXES_COLOUR = '#6E6E6E'
    PLOT_AXES_LABEL_COLOUR = '#404040'
    # set axis colours
    for k in ax.spines.keys():
        ax.spines[k].set_color(PLOT_AXES_COLOUR)
    # Set colour of tick marks
    ax.tick_params(axis='both', colors=PLOT_AXES_LABEL_COLOUR)
    # Set colour of tick labels
    ax.xaxis.label.set_color(PLOT_AXES_LABEL_COLOUR)
    ax.yaxis.label.set_color(PLOT_AXES_LABEL_COLOUR)
    ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,g}'))
    # add grids
    ax.grid(b=True, which='major',axis='both', color=PLOT_GRID_COLOUR)
    # Puts the grids below all other drawn elements
    # False would put it above all (default)
    # 'line' would put it above areas but below lines
    ax.set_axisbelow(True)
    # add legend
    # Shrink height of plot to accomodate legend outside of plot area
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width, box.height * 0.95])
    # add grids
    # ax.grid(b=True, which='major',axis='y', color=PLOT_GRID_COLOUR)
    # add legend
    if ncols > 0:
        leg = fig.legend(loc='upper center',markerscale = PLOT_LEGEND_MARKERSCALE,
                bbox_to_anchor=(0.53,1.0), ncol=ncols)
        leg.get_frame().set_edgecolor(PLOT_AXES_COLOUR)

'''