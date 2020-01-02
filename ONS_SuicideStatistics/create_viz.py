import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Polygon, PathPatch
from matplotlib.path import Path


def load_data():
    fpath = os.path.join(os.getcwd(), 'ONS_SuicideStatistics', 'data',
                         'ONS_UK_SuicideStatistics.csv')

    data = pd.read_csv(fpath)
    # the first and last indices of Age are strings <10 and 90+
    # <10 has no data (all zeroes)
    # 90+ will be plotted at 90 anyway. The + can be reflected by
    # changing the axis tick labels. int type for age will be easier
    # to deal with than str type.
    data = data.drop(0)
    data.loc[data.index[-1], 'Age'] = 90
    data = data.astype({'Age': int})

    return data


def create_plot():
    df = load_data()
    years = df.columns.values[~df.columns.isin(['Age'])]
    cmap = cm.get_cmap('Blues', 150)
    nrows = len(years)
    fig, axes = plt.subplots(nrows=nrows, figsize=(15, 0.5*nrows), sharex=True)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.08, right=0.95, hspace=-0.8)

    a,b = 10, 90
    for axis, year in zip(axes, years):
        axis.plot(df['Age'], df[year], c='#FFFFFF', alpha=0)
        axis.autoscale(False)
        axis.patch.set_alpha(0)

        poly_vertices = [(a, 0)] + list(zip(df['Age'], df[year])) + [(b, 0)]
        polygon = Polygon(poly_vertices, color='none')
        patch = axis.add_patch(polygon)

        img = np.expand_dims(df['Age'].values, axis=1)
        axis.imshow(img, cmap=cmap, origin='lower', aspect='auto', 
                clip_path=patch, clip_on=True, extent=[10,90,0,150])

    # TODO: Remove splines for all axes
    # TODO: Add spline for bottom-most axis
    # TODO: Add text/annotation at end of each plot to display the year
    # TODO: Modify ticks & tick labels to show every year/10 years, and show <10 and 90+
    # TODO: Smooth curves
    # TODO: Make plot interactive

    fpath = os.path.join(os.getcwd(), 'Output_Figures', 'SuicityStatistics.png')
    fig.savefig(fpath, bbox_inchex='auto', pad_inches=0)


if __name__ == '__main__':
    create_plot()
