import boto3
import botocore.exceptions
import json
from pkg_resources import resource_filename

regions = ['us-east-1', 'us-east-2',
           'us-west-1', 'us-west-2',
           'ca-central-1',
           'eu-central-1', 'eu-central-2',
           'eu-west-1', 'eu-west-2', 'eu-west-3',
           'eu-north-1',
           'eu-south-1', 'eu-south-2',
           'af-south-1',
           'ap-east-1',
           'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
           'ap-south-1', 'ap-south-2',
           'ap-southeast-1', 'ap-southeast-2', 'ap-southeast-3', 'ap-southeast-4',
           'il-central-1',
           'me-south-1',
           'me-central-1',
           'sa-east-1',
           #'us-gov-east-1', 'us-gov-west-1'
           ]

excluded_regions = ['cn-north-1']

excluded_location_types = ['AWS Wavelength Zone', 'AWS Local Zone']


instance_types = ['i3en.large', 'i3en.xlarge', 'i3en.2xlarge', 'i3en.3xlarge', 'i3en.6xlarge', 'i3en.12xlarge',
                  'i3en.24xlarge', 'i3en.metal',
                  'im4gn.large', 'im4gn.xlarge', 'im4gn.2xlarge', 'im4gn.4xlarge', 'im4gn.8xlarge', 'im4gn.16xlarge',
                  'is4gen.medium', 'is4gen.large', 'is4gen.xlarge', 'is4gen.2xlarge', 'is4gen.4xlarge', 'is4gen.8xlarge',
                  'i4i.large', 'i4i.xlarge', 'i4i.2xlarge', 'i4i.4xlarge', 'i4i.8xlarge', 'i4i.12xlarge', # not all i4i
                  'm7gd.medium', 'm7gd.large', 'm7gd.xlarge', 'm7gd.2xlarge', 'm7gd.4xlarge', 'm7gd.8xlarge',
                  'm7gd.12xlarge', 'm7gd.16xlarge',
                  'd3.xlarge', 'd3.2xlarge', 'd3.4xlarge', 'd3.8xlarge',
                  'd3en.xlarge', 'd3en.2xlarge', 'd3en.4xlarge', 'd3en.6xlarge', 'd3en8xlarge', 'd3en.12xlarge',
                  'm5.large', 'm5.xlarge', 'm5.2xlarge', 'm5.4xlarge', # instances recommended by CFLT
                  'c5.large', 'c5.xlarge', 'c5.2xlarge', 'c5.4xlarge', # instances recommended by CFLT
                  'r5.large', 'r5.xlarge', 'r5.2xlarge', 'r5.4xlarge', 'r5.8xlarge', # instances recommended by CFLT
                  # instances used by BYOC connectors
                  'c5.9xlarge', 'c5.12xlarge', 'c5.18xlarge', 'c5.24xlarge', # other instances (maybe for KC connectors?)
                  ]

# The basis for this was found on SO:
# https://stackoverflow.com/questions/51673667/use-boto3-to-get-current-price-for-given-ec2-instance-type

# Search product filter. This will reduce the amount of data returned by the
# get_products function of the Pricing API
FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},' \
      '{{"Field": "operatingSystem", "Value": "{o}", "Type": "TERM_MATCH"}},' \
      '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},' \
      '{{"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}}]'


# Translate region code to region name. Even though the API data contains
# regionCode field, it will not return accurate data. However using the location
# field will, but then we need to translate the region code into a region name.
# You could skip this by using the region names in your code directly, but most
# other APIs are using the region code.
def get_region_name(region_code):
    default_region = 'US East (N. Virginia)'
    endpoint_file = resource_filename('botocore', 'data/endpoints.json')
    try:
        with open(endpoint_file, 'r') as f:
            data = json.load(f)
        # Botocore is using Europe while Pricing API using EU...sigh...
        return data['partitions'][0]['regions'][region_code]['description'].replace('Europe', 'EU')
    except IOError:
        return default_region


def getOnDemandPrice(od_pricing_block):

    # on demand pricing is tricky

    try:
        onDemandCode = list(od_pricing_block)[0]
        onDemandSubCode = list(od_pricing_block[onDemandCode]['priceDimensions'])[0]
        onDemandPrice = od_pricing_block[onDemandCode]['priceDimensions'][onDemandSubCode]['pricePerUnit']['USD']

        # print(onDemandPrice)
        return onDemandPrice

    except KeyError:
        raise

def getRIprice(term, ri_pricing_block):

    # RI pricing is even trickier
    for k in ri_pricing_block:

        try:
            if (ri_pricing_block[k]['termAttributes']['LeaseContractLength'] == term and
                    ri_pricing_block[k]['termAttributes']['OfferingClass'] == 'standard' and
                    ri_pricing_block[k]['termAttributes']['PurchaseOption'] == 'No Upfront'):
                pd = ri_pricing_block[k]['priceDimensions']
                riCode = list(ri_pricing_block[k]['priceDimensions'])[0]

                ri_price = ri_pricing_block[k]['priceDimensions'][riCode]['pricePerUnit']['USD']
                #print(ri_price)

                return ri_price
        except KeyError:
            print(ri_pricing_block)
            # TODO:  need to identify which regions cause this problem
            raise

def main():

    client = boto3.client('pricing', region_name='us-east-1')

    f = FLT.format(o='Linux')
    next_token = None

    vm_attribs = []

    while True:
        params = {'ServiceCode': 'AmazonEC2', 'Filters': json.loads(f)}

        if next_token:
            params['NextToken'] = next_token

        data = client.get_products(**params)
        next_token = data.get('NextToken')

        price_list = data['PriceList']

        for productStr in price_list:
            product = json.loads(productStr)

            # Allowing all reagions introduces all sorts of odd stuff like non-USD currencies and no Reserved instances
            # best to just explicitly list the ones you want, and exclude the ones you don't
            if product['product']['attributes']['instanceType'] in instance_types and \
                    product['product']['attributes']['regionCode'] in regions and \
                    product['product']['attributes']['regionCode'] not in excluded_regions and \
                    product['product']['attributes']['locationType'] not in excluded_location_types:

                try:
                    attrib = [product['product']['attributes']['regionCode'],
                              product['product']['attributes']['instanceType'],
                              product['product']['attributes']['vcpu'],
                              product['product']['attributes']['memory'].replace('GiB', '').strip(),
                              getOnDemandPrice(product['terms']['OnDemand']), # on demand pricing
                              getRIprice('1yr', product['terms']['Reserved']), # 1 yr ri
                              getRIprice('3yr', product['terms']['Reserved']), # 3 yr ri
                              product['product']['attributes']['storage'],
                              product['product']['attributes']['location'],
                              ]
                    vm_attribs.append(attrib)

                    #print(attrib)

                except KeyError:
                    print(product)
                    raise

        if not next_token:
            break

    sorted_vm_list = sorted(vm_attribs, key=lambda x: (x[0], x[1]))

    for vm in sorted_vm_list:
        print( ','.join(vm))


if __name__ == "__main__":
    main()
