import requests


instance_families = [{'family': 'Las v3', 'query_string_ext': "and productName eq 'Lasv3 Series Linux'"
                                        , 'instances': ['Standard_L8as_v3',
                                                        'Standard_L16as_v3',
                                                        'Standard_L32as_v3',
                                                        'Standard_L48as_v3',
                                                        'Standard_L64as_v3',
                                                        'Standard_L80as_v3']
                                        , 'regions': []},
                     {'family': 'Fs v2', 'query_string_ext': "and productName eq 'Virtual Machines FSv2 Series'"
                                       , 'instances': ['Standard_F2s_v2',
                                                       'Standard_F4s_v2',
                                                       'Standard_F8s_v2',
                                                       'Standard_F16s_v2',
                                                       'Standard_F32s_v2',
                                                       'Standard_F48s_v2',
                                                       'Standard_F72s_v2']
                                       , 'regions': ['northcentralus',
                                                     'eastus',
                                                     'norwayeast',
                                                     'uksouth']},

                  ]


def convertToHourlyRate(term, rate):

    # TODO:  should probably validate that the term is hours using the unitOfMeasure field, but it's always hours...

    if term == '1 Year':
        hourly_rate = round(rate / 365 / 24, 4)
    elif term == '3 Years':
        hourly_rate = round(rate / (3 * 365) / 24, 4)
    else:
        hourly_rate = rate

    return hourly_rate


def main():
    # api_url = "https://prices.azure.com/api/retail/prices?api-version=2021-10-01-preview"
    api_url = 'https://prices.azure.com/api/retail/prices'
    next_url = api_url

    vm_attribs = []

    for family in instance_families:

        for instance in family['instances']:

            query = f"armSkuName eq '{instance}' {family['query_string_ext']}"

            while next_url:
                response = requests.get(next_url, params={'$filter': query})

                if response.status_code == 200:
                    pricing_data = response.json()
                    #print(pricing_data)

                    for item in pricing_data['Items']:
                        if 'Low Priority' not in item['skuName'] and \
                                'Spot' not in item['skuName']:

                            term = item.get('reservationTerm', 'On Demand')
                            hourly_rate = convertToHourlyRate(term=term, rate=item['unitPrice'])


                            # We may not want all regions for all instance types
                            # i.e. only BYOC uses Fs types for managed connectors so regions where BYOC doesn't exist
                            #      might not be relevant, and if there are lots of instances the table will get big
                            # if no regions are included for the instance family, then ALL regions will be included
                            if item['armRegionName'] in family.get('regions', '') or \
                                family.get('regions', '') == '':

                                attrib = [item['armRegionName'],
                                          item['location'],
                                          item['meterName'],
                                          item['skuName'],
                                          term,
                                          str(hourly_rate),
                                          ]

                                vm_attribs.append(attrib)

                    if 'nextLink' in pricing_data:
                        next_url = pricing_data['nextLink]']

                    else:
                        break

    # sorting the output by region, instance, & term is not required, but helps with troubleshooting in Ubercalc
    sorted_vm_pricing = sorted(vm_attribs, key=lambda x: (x[1], x[2], x[4]))

    for vm in sorted_vm_pricing:
        print( ','.join(vm))


if __name__ == "__main__":
    main()
