import datetime
import numpy as np
from astropy.io import ascii
from matplotlib import pyplot as plt

# To do: label axes with colors

d = ((1,28,13),
     (2,13,13),
     (2,24,13),
     (4,3,13),
     (4,20,13),
     (5,27,13),
     (7,4,13),
     (8,9,13),
     (8,17,13),
     (10,26,13),
     (11,22,13),
     (11,9,13),
     (12,8,13),
     (12,19,13),
     (1,4,14),
     (1,22,14),
     (2,7,14),
     (2,25,14)
     )
gasmask = [True,True,False,False,False,False,False,False,False,False,False,False,False,False,False,False,True,False]
dates = np.ma.array([datetime.date(2000+dd[2],dd[0],dd[1]) for dd in d])

gallons = np.ma.array((13.349,12.743,13.232,12.991,13.283,12.551,12.507,12.482,12.595,13.998,12.813,11.324,12.784,13.885,11.270,13.974,0,13.645),mask=gasmask)
mileage = np.ma.array((235.7,254.6,259.1,270.9,281.5,270.9,270.9,287.5,352.4,292.1,235.7,265.3,251.2,269.1,134.4,202.4,249.6,248.4),mask=gasmask)

dates.sort()
gallons = np.ma.array([g for (d,g) in zip(dates,gallons)],mask=gasmask)
mileage = np.ma.array([m for (d,m) in zip(dates,mileage)],mask=gasmask)

mpg = mileage/gallons

pricedata = [0,0,3.72,3.59,3.37,3.89,3.27,3.43,3.54,3.13,3.09,2.99,2.93,2.99,3.25,3.18,0,3.55]
price = np.ma.array([p + 0.009 for p in pricedata],mask=gasmask)

# http://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EMM_EPMRU_PTE_R20_DPG&f=W

ngp_path = './data'
national_gas_price_file = '%s/Weekly_Midwest_Regular_Conventional_Retail_Gasoline_Prices.csv' % ngp_path
ngp = ascii.read(national_gas_price_file,data_start = 5)
ngp_dates = [datetime.datetime.strptime(d,'%m/%d/%Y') for d in ngp['col1']]
ngp_price = ngp['col2']

# Start of 2013

istart = 0
for idx,n in enumerate(ngp_dates):
    if n == datetime.datetime(2013, 1, 7, 0, 0):
        istart = idx

fig,ax1 = plt.subplots()
ln1 = ax1.plot(dates,mpg,color='b',linewidth=2,linestyle='--',label='Lexus MPG')
ax1.set_xlabel('Date')
ax1.set_ylabel('Miles per gallon')

# Example of how to do this: http://matplotlib.org/examples/api/two_scales.html

ax2 = ax1.twinx()
ln2 = ax2.plot(dates,price,color='r',linewidth=2,label='Price paid')
#ln3 = ax2.plot(ngp_dates[:istart],ngp_price[:istart],color='g',label='Average price in Midwest')
ax2.set_ylabel('Gas price [$/gal]')

lns = ln1+ln2#+ln3
labs = [l.get_label() for l in lns]
ax2.legend(lns, labs, loc=8)

plt.show()

