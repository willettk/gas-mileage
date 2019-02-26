import datetime
import sys,getopt

import numpy as np
from matplotlib import pyplot as plt

inputDataPath = './data'

'''Todo:

    save the updated gas prices in identical format

'''

def getRegions():

    r = [{'startDate':datetime.datetime(2011,7,1),
            'endDate':datetime.datetime(2016,12,1),
            'region_name': 'Midwest',
            'region_code':'20'},
         {'startDate':datetime.datetime(2016,12,1),
            'endDate':datetime.datetime(2116,12,1),
            'region_name': 'West Coast less California',
            'region_code':'5XCA'}]

    return r

def update_gas_prices(region_code):

    import urllib2
    import itertools
    from bs4 import BeautifulSoup

    url = "http://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EMM_EPM0U_PTE_R{}_DPG&f=W".format(region_code)
    page = urllib2.urlopen(url).read()
    soup = BeautifulSoup(page,"lxml")

    months = soup.find_all('td',{"class":"B6"})
    days = soup.find_all('td',{"class":"B5"})
    values = soup.find_all('td',{"class":"B3"})

    # Expand so the months and years match the number of cells for price data
    m5 = [[x.text.strip()]*5 for x in months]
    months_expanded = list(itertools.chain(*m5))

    # Remove empty cells for months without a fifth week of data

    for m,d,v in zip(months_expanded,days,values):
        if d.text.strip() is u'':
            months_expanded.remove(m)
            days.remove(d)
            values.remove(v)

    # Format date and price data into numpy arrays
    d_str = ['%s %s' % (m,d.text.strip()[-2:]) for m,d in zip(months_expanded,days)]
    ngp_dates = [datetime.datetime.strptime(d,'%Y-%b %d') for d in d_str]

    v_str = [v.text.strip() for v in values]
    ngp_price = [float(v) if v is not u'' else 0. for v in v_str]

    return ngp_dates,ngp_price

def combine_gas_region_prices():

    regions = getRegions()
    all_dates,all_prices = [],[]
    for r in regions:
        print "Loading gas price data for {} region".format(r['region_name'])
        ngp_dates,ngp_price = update_gas_prices(r['region_code'])
        truthArray = [True if x > r['startDate'] and x <= r['endDate'] else False for x in ngp_dates]
        for t,d,p in zip(truthArray,ngp_dates,ngp_price):
            if t:
                all_dates.append(d)
                all_prices.append(p)

    return all_dates,all_prices

def load_gas_prices():

    from astropy.io import ascii

    # Source of data:
    #
    # http://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EMM_EPMRU_PTE_R20_DPG&f=W
    # Select hamburger menu on right of screen above graph to download CSV data

    national_gas_price_file = '%s/Weekly_Midwest_Regular_Conventional_Retail_Gasoline_Prices.csv' % inputDataPath
    ngp = ascii.read(national_gas_price_file,data_start = 5)
    ngp_dates = [datetime.datetime.strptime(d,'%m/%d/%Y') for d in ngp['col1']]
    ngp_price = ngp['col2']

    # Reverse them so that they're sorted from oldest to newest (same format as web-based data)

    ngp_dates_rev = ngp_dates[::-1]
    ngp_price_rev = ngp_price[::-1]

    return ngp_dates_rev,ngp_price_rev

def main(argv):

    try:
       opts, args = getopt.getopt(argv,"u")
    except getopt.GetoptError:
       print 'python gasmileage.py [-u]'
       sys.exit(2)
    if len(opts) > 0:
        for opt, arg in opts:
           if opt == '-u':
               #ngp_dates,ngp_price = update_gas_prices()
               #print "\nDownloading updated gas price data from http://www.eia.gov\n"
               ngp_dates,ngp_price = combine_gas_region_prices()
    else:
        ngp_dates,ngp_price = load_gas_prices()
        print "\nUsing archived gas price data from %s \n" % datetime.datetime.strftime(ngp_dates[-1],'%Y-%m-%d')

    # Import personal data on gas prices, mileage, and distance

    d = np.genfromtxt('%s/gas_subaru.txt' % inputDataPath,delimiter=',',names=('month','day','year','gallons','mileage','price'))

    my_dates = np.array([datetime.date(2000+int(Y),int(M),int(D)) for Y,M,D in zip(d['year'],d['month'],d['day'])])

    gallons = d['gallons']
    mileage = d['mileage']
    price = d['price'] + 0.009
   
    # Limit gas price data to after when I purchased the car

    istart = 0
    for idx,n in enumerate(ngp_dates):
        if n == datetime.datetime(2014, 3, 10, 0, 0):
            istart = idx

    # Mask out data if either the mileage or volume of refill is missing
    mask1 = np.isfinite(mileage) & np.isfinite(gallons)

    fig = plt.figure(1,(12,8))

    # Plot miles per gallon for each time car is refueled

    ax1 = fig.add_subplot(211)

    mpg = np.array([m/g for m,g in zip(mileage,gallons)])
    ax1.plot(my_dates[mask1],mpg[mask1],color='C0',linewidth=2)

    # Info for 2014 Subaru Wagon with manual transmission is from
    # http://www.fueleconomy.gov/feg/Find.do?action=sbs&id=34225

    mpg_city,mpg_hwy,mpg_comb = 25,33,28

    ax1.text(my_dates[mask1][0],mpg_city,'  city',    color='black',va = 'baseline',ha='left',size='small')
    ax1.text(my_dates[mask1][0],mpg_hwy, '  highway', color='black',va = 'baseline',ha='left',size='small')
    ax1.text(my_dates[mask1][0],mpg_comb,'  combined',color='black',va = 'baseline',ha='left',size='small')

    ax1.axhline(mpg_city,color='black',linestyle='-',lw=1)
    ax1.axhline(mpg_comb,color='black',linestyle='--',lw=1)
    ax1.axhline(mpg_hwy,color='black',linestyle='-',lw=1)

    ax1.set_xlabel('Date')
    ax1.set_ylabel('Miles per gallon')
    ax1.set_title('Mileage for Subaru Impreza',fontsize=22)
    ax1.set_ylim(20,35)

    # Plot price paid for gasoline

    ax2 = fig.add_subplot(212)
    mask2 = np.isfinite(price)
    ln_my_price = ax2.plot(my_dates[mask2],price[mask2],color='C1',linewidth=2,label='Price I paid')
    ln_avg_price = ax2.plot(ngp_dates[istart:],ngp_price[istart:],color='C2',label='Average price in region')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Gas price [$/gal]')
    ax2.set_title('Prices for gasoline',fontsize=22)

    lns = ln_my_price + ln_avg_price
    labs = [l.get_label() for l in lns]
    ax2.legend(lns, labs, loc='best',fontsize='medium')


    # How much money have I lost/saved compared to the regional average?

    amount_i_paid = (gallons[mask2] * price[mask2]).sum()

    amount_expected = 0
    for d,g,p in zip(my_dates[mask2],gallons[mask2],price[mask2]):
        d_datetime = datetime.datetime.combine(d,datetime.datetime.min.time())
        i = np.argmin(abs(d_datetime - np.array(ngp_dates)))
        amount_expected += (ngp_price[i] * g)
        #print("{:.2f} avg, {:.2f} paid; diff = {:7.2f}".format(ngp_price[i] * g,p*g,(ngp_price[i]-p)*g))

    print("Total amount I actually paid             : {:.2f}".format(amount_i_paid))
    print("Total amount I would have expected to pay: {:.2f}".format(amount_expected))
    amount_saved = "${:.2f}".format(amount_expected - amount_i_paid)
    print("Average per fill-up: ${:.2f} ({} trips)".format((amount_expected - amount_i_paid)/mask2.sum(),mask2.sum()))
    cg = 'g' if amount_saved > 0 else 'r'
    ax2.text(my_dates[mask2][int(mask2.sum()*0.8)],2.0,"Money saved: ", color='k' ,va = 'baseline',ha='right',size='large')
    ax2.text(my_dates[mask2][int(mask2.sum()*0.8)],2.0,amount_saved, color=cg ,va = 'baseline',ha='left',size='large')

    # Fix final figure parameters
    fig.set_tight_layout(True)
    plt.show()

if __name__ == "__main__":
   main(sys.argv[1:])