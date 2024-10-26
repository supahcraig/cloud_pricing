import boto3
import botocore.exceptions
import json
import datetime
from alive_progress import alive_bar
from instances import aws_instances
from regions import aws_regions


excluded_regions = ['cn-north-1']

excluded_location_types = ['AWS Wavelength Zone', 'AWS Local Zone']

# The basis for this was found on SO:
# https://stackoverflow.com/questions/51673667/use-boto3-to-get-current-price-for-given-ec2-instance-type

# Search product filter. This will reduce the amount of data returned by the
# get_products function of the Pricing API
FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},' \
      '{{"Field": "operatingSystem", "Value": "{o}", "Type": "TERM_MATCH"}},' \
      '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},' \
      '{{"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}}]'


def get_on_demand_price(od_pricing_block):

    # on demand pricing is tricky
    # the OnDemand pricing payload is embedded under some sort of serial # key in the json
    # it's the only key at this level, so it's safe to turn it into a list and grab the first element
    # that element will the the "serial #" which can then be fed back into the dictionary to get the price
    onDemandCode = list(od_pricing_block)[0]
    onDemandSubCode = list(od_pricing_block[onDemandCode]['priceDimensions'])[0]
    onDemandPrice = od_pricing_block[onDemandCode]['priceDimensions'][onDemandSubCode]['pricePerUnit']['USD']

    # print(onDemandPrice)
    return onDemandPrice


def get_ri_price(term, ri_pricing_block):

    # RI pricing is even trickier
    for k in ri_pricing_block:

        if (ri_pricing_block[k]['termAttributes']['LeaseContractLength'] == term and
                ri_pricing_block[k]['termAttributes']['OfferingClass'] == 'standard' and
                ri_pricing_block[k]['termAttributes']['PurchaseOption'] == 'No Upfront'):

            # the RI pricing payload is embedded under some sort of serial # key in the json
            # it's the only key at this level, so it's safe to turn it into a list and grab the first element
            # that element will the the "serial #" which can then be fed back into the dictionary to get the price
            ri_code = list(ri_pricing_block[k]['priceDimensions'])[0]
            ri_price = ri_pricing_block[k]['priceDimensions'][ri_code]['pricePerUnit']['USD']
            #print(ri_price)

            return ri_price


def main():

    # the client must be created out of only specific regions, us-east-1 is one of them.
    client = boto3.client('pricing', region_name='us-east-1')

    f = FLT.format(o='Linux')
    next_token = None

    vm_attribs = []

    with alive_bar(title='Fetching EC2 data from AWS...', spinner='dots') as bar:
        while True:
            bar()
            params = {'ServiceCode': 'AmazonEC2', 'Filters': json.loads(f)}

            if next_token:
                params['NextToken'] = next_token

            try:
                data = client.get_products(**params)
                next_token = data.get('NextToken')

            except botocore.exceptions.UnauthorizedSSOTokenError as e:
                print("Your AWS session has expired.")
                exit(98)

            price_list = data['PriceList']

            for productStr in price_list:
                product = json.loads(productStr)

                # Allowing all regions introduces all sorts of odd stuff like non-USD currencies and no RI's
                # best to just explicitly list the ones you want, and exclude the ones you don't
                if product['product']['attributes']['instanceType'] in aws_instances and \
                        product['product']['attributes']['regionCode'] in aws_regions and \
                        product['product']['attributes']['regionCode'] not in excluded_regions and \
                        product['product']['attributes']['locationType'] not in excluded_location_types:

                    try:
                        attrib = [
                                  product['product']['attributes']['location'],
                                  product['product']['attributes']['regionCode'],
                                  product['product']['attributes']['instanceType'],
                                  product['product']['attributes']['vcpu'],
                                  product['product']['attributes']['memory'].replace('GiB', '').strip(),
                                  get_on_demand_price(product['terms']['OnDemand']), # on demand pricing
                                  get_ri_price('1yr', product['terms']['Reserved']), # 1 yr ri
                                  get_ri_price('3yr', product['terms']['Reserved']), # 3 yr ri
                                  product['product']['attributes']['storage'],
                                  ]
                        vm_attribs.append(attrib)

                        #print(attrib)

                    except KeyError:
                        # not even trying to handle the error, just show the problematic payload
                        print(product)
                        raise

            if not next_token:
                break

    # Sort by region code & instance type.  Sorting is not required, but makes it easier to troubleshoot the Ubercalc
    sorted_vm_list = sorted(vm_attribs, key=lambda x: (x[1], x[2]))

    # You will want to paste the "prices as of" as well as the header row.  
    print(f'PRICES AS OF {datetime.datetime.now():%m/%d/%Y}')
    print(','.join(['Region Name',
                    'Region',
                    'Instance Type',
                    'Cores',
                    'Memory (GB)',
                    'On Demand',
                    '1 Year RI',
                    '3 Year RI',
                    'Instance Store Capacity']
                   )
          )

    for vm in sorted_vm_list:
        print( ','.join(vm))


if __name__ == "__main__":
    main()
