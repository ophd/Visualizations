import os, re
import pandas as pd
import matplotlib.pyplot as plt

def load_data():
    ''' Load the OECD life expectancy data from file '''
    f_path_name = os.path.join(os.getcwd(), 'OECD_LifeExpenctancy', 'OECD_LifeExpectancy_data.csv')

    return pd.read_csv(f_path_name)


def dotplot(df):
    pass



if __name__ == '__main__':
    df = load_data()
    
    # Get list of top ten countries for 2010 by total life expectancy at birth
    top10 = df.loc[(df['TIME'] == 2010) & (df['SUBJECT'] == 'TOT')]
              .sort_values(by='Value', ascending=False)
              .iloc[:10]['LOCATION']
    