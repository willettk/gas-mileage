# gas-mileage
Tracking the gas mileage and performance for my cars.

### Running code

```bash
> python gas_mileage.py [-u]
```

Set the `-u` flag to update the analysis to use the latest gas prices nationwide for comparison. 

### Data sources

* Mileage, price paid, and amount of gas per fillup are recorded manually each time car is refueled and then transferred to the CSV files in `.data/`. 
* Nationwide data for gas prices in the USA is scraped from the websites of the [U.S. Energy Information Administration](https://www.eia.gov/)
