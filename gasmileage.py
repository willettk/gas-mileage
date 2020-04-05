import datetime
import sys
import getopt
import urllib2
import itertools
import csv

import numpy as np
from matplotlib import pyplot as plt
from bs4 import BeautifulSoup

inputDataPath = './data'
cachedGasPriceFile = '{}/cached_gas_prices.csv'.format(inputDataPath)

ymdFormat = '%Y-%m-%d'


def get_regions():

    r = [{'startDate': datetime.datetime(2011, 7, 1),
          'endDate': datetime.datetime(2016, 12, 1),
          'region_name':  'Midwest',
          'region_code': '20'},
         {'startDate': datetime.datetime(2016, 12, 1),
          'endDate': datetime.datetime(2116, 12, 1),
          'region_name':  'West Coast less California',
          'region_code': '5XCA'}]

    return r


def update_gas_prices(region_code):
    """
    Raw source of data is EIA website

    Select hamburger menu on right of screen above graph to download CSV data
    on the webpage.
    """

    url = f"http://www.eia.gov/dnav/pet/hist/LeafHandler.ashx" + \
        "?n=PET&s=EMM_EPM0U_PTE_R{region_code}_DPG&f=W"
    page = urllib2.urlopen(url).read()
    soup = BeautifulSoup(page, "lxml")

    months = soup.find_all('td', {"class": "B6"})
    days = soup.find_all('td', {"class": "B5"})
    values = soup.find_all('td', {"class": "B3"})

    # Expand so the months and years match the number of cells for price data
    m5 = [[x.text.strip()]*5 for x in months]
    months_expanded = list(itertools.chain(*m5))

    # Remove empty cells for months without a fifth week of data

    for m, d, v in zip(months_expanded, days, values):
        if d.text.strip() == u'':
            months_expanded.remove(m)
            days.remove(d)
            values.remove(v)

    # Format date and price data into numpy arrays
    d_str = ['{} {}'.format(m, d.text.strip()[-2:])
             for m, d in zip(months_expanded, days)]
    ngp_dates = [datetime.datetime.strptime(d, '%Y-%b %d') for d in d_str]

    v_str = [v.text.strip() for v in values]
    ngp_prices = [float(v) if v != u'' else 0. for v in v_str]

    return ngp_dates, ngp_prices


def combine_gas_region_prices(verbose=True):

    regions = get_regions()
    all_dates, all_prices = [], []
    for r in regions:
        if verbose:
            print("Loading gas price data for {} region".format(r['region_name']))
        ngp_dates, ngp_prices = update_gas_prices(r['region_code'])
        truthArray = [True if x > r['startDate'] and x <= r['endDate'] else False for x in ngp_dates]
        for t, d, p in zip(truthArray, ngp_dates, ngp_prices):
            if t:
                all_dates.append(d)
                all_prices.append(p)

    return all_dates, all_prices


def load_gas_prices(filename=cachedGasPriceFile):
    """
    Load data from local file as of the last update call.
    """

    with open(filename, 'r') as f:
        ngp = f.readlines()
    ngp = [n.strip().split(',') for n in ngp]
    ngp_dates = [datetime.datetime.strptime(n[0], ymdFormat) for n in ngp]
    ngp_prices = [float(n[1]) for n in ngp]

    return ngp_dates, ngp_prices


def plot_gas_mileage(dates, prices):

    # Import personal data on gas prices, mileage, and distance

    d = np.genfromtxt('{}/gas_subaru.txt'.format(inputDataPath), delimiter=',', names=('month', 'day', 'year', 'gallons', 'mileage', 'price'))

    my_dates = np.array([datetime.date(2000+int(Y), int(M), int(D)) for Y, M, D in zip(d['year'], d['month'], d['day'])])

    gallons = d['gallons']
    mileage = d['mileage']
    price = d['price'] + 0.009

    # Limit gas price data to after when I purchased the car

    istart = 0
    for idx, n in enumerate(dates):
        if n == datetime.datetime(2014, 3, 10, 0, 0):
            istart = idx

    # Mask out data if either the mileage or volume of refill is missing
    mask1 = np.isfinite(mileage) & np.isfinite(gallons)

    fig = plt.figure(1, (12, 8))

    # Plot miles per gallon for each time car is refueled

    ax1 = fig.add_subplot(211)

    mpg = np.array([m/g for m, g in zip(mileage, gallons)])
    ax1.plot(my_dates[mask1], mpg[mask1], color='C0', linewidth=2)

    """
    Info for 2014 Subaru Wagon with manual transmission is from
    http://www.fueleconomy.gov/feg/Find.do?action=sbs&id=34225
    """

    mpg_city, mpg_hwy, mpg_comb = 25, 33, 28

    ax1.text(my_dates[mask1][0], mpg_city, '  city', color='grey', va='baseline', ha='left', size='small')
    ax1.text(my_dates[mask1][0], mpg_hwy,  '  highway', color='grey', va='baseline', ha='left', size='small')
    ax1.text(my_dates[mask1][0], mpg_comb, '  combined', color='grey', va='baseline', ha='left', size='small')

    # Actual miles per gallon

    mpg_actual = sum(mileage[mask1]) / sum(gallons[mask1])
    ax1.text(my_dates[mask1][0], mpg_actual, '  actual', color='black', va='baseline', ha='left', size='small')

    ax1.axhline(mpg_city, color='grey', linestyle='-', lw=1)
    ax1.axhline(mpg_comb, color='grey', linestyle='--', lw=1)
    ax1.axhline(mpg_hwy, color='grey', linestyle='-', lw=1)
    ax1.axhline(mpg_actual, color='black', linestyle='-.', lw=1)

    ax1.set_xlabel('Date')
    ax1.set_ylabel('Miles per gallon')
    ax1.set_title('Mileage for Subaru Impreza', fontsize=22)
    ax1.set_ylim(20, 38)

    # Plot price paid for gasoline

    ax2 = fig.add_subplot(212)
    mask2 = np.isfinite(price)
    ln_my_price = ax2.plot(my_dates[mask2], price[mask2], color='C1', linewidth=2, label='Price I paid')
    ln_avg_price = ax2.plot(dates[istart:], prices[istart:], color='C2', label='Average price in region')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Gas price [$/gal]')
    ax2.set_title('Prices for gasoline', fontsize=22)

    lns = ln_my_price + ln_avg_price
    labs = [l.get_label() for l in lns]
    ax2.legend(lns, labs, loc='best', fontsize='medium')

    # How much money have I lost/saved compared to the regional average?

    amountActuallyPaid = (gallons[mask2] * price[mask2]).sum()

    amountExpectedPaid = 0
    for d, g, p in zip(my_dates[mask2], gallons[mask2], price[mask2]):
        d_datetime = datetime.datetime.combine(d, datetime.datetime.min.time())
        i = np.argmin(abs(d_datetime - np.array(dates)))
        amountExpectedPaid += (prices[i] * g)

    print("Total amount I actually paid             : {:.2f}".format(amountActuallyPaid))
    print("Total amount I would have expected to pay: {:.2f}".format(amountExpectedPaid))
    amountSaved = "${:.2f}".format(amountExpectedPaid - amountActuallyPaid)
    print("Average per fill-up: ${:.2f} ({} trips)".format((amountExpectedPaid - amountActuallyPaid)/mask2.sum(), mask2.sum()))
    cg = 'g' if amountSaved > 0 else 'r'
    ax2.text(my_dates[mask2][int(mask2.sum()*0.8)], 2.0, "Money saved: ", color='k', va='baseline', ha='right', size='large')
    ax2.text(my_dates[mask2][int(mask2.sum()*0.8)], 2.0, amountSaved, color=cg, va='baseline', ha='left', size='large')

    # Fix final figure parameters
    fig.set_tight_layout(True)
    plt.show()

    return None


def main(argv):

    try:
        opts, args = getopt.getopt(argv, "u")
    except getopt.GetoptError:
        print('python gasmileage.py [-u]')
        sys.exit(2)
    if len(opts) > 0:
        for opt, arg in opts:
            if opt == '-u':
                # Scrape the EIA website and get updated national avg gas prices
                try:
                    ngp_dates, ngp_prices = combine_gas_region_prices()

                    # Save results to new file

                    with open(cachedGasPriceFile, 'w') as wf:
                        writer = csv.writer(wf, delimiter=',')
                        ngp_dates_str = [datetime.datetime.strftime(d, ymdFormat) for d in ngp_dates]
                        for d, p in zip(ngp_dates_str, ngp_prices):
                            writer.writerow([d, p])
                except:
                    print("Exception when trying to download new gas prices.")
    else:
        # Use local copy of whatever data was scraped most recently
        ngp_dates, ngp_prices = load_gas_prices()
        print("\nUsing local file with gas price data; current through {}. \n".format(datetime.datetime.strftime(ngp_dates[-1], ymdFormat)))

    # Create plot

    plot_gas_mileage(ngp_dates, ngp_prices)

    return None


if __name__ == "__main__":
    main(sys.argv[1:])
