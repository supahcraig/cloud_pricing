aws_instances  = ['i3en.large', 'i3en.xlarge', 'i3en.2xlarge', 'i3en.3xlarge', 'i3en.6xlarge', 'i3en.12xlarge',
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

gcp_instances = ['N2',
                 'N2D AMD']


# For Azure you can include a list of regions for a specific instance family that you want
# if you leave it empty it will pull pricing for all regions
# A typical use for this is that the Fs_v2 instances are used for BYOC connectors,
#   but BYOC is only available in 4 Azure regions
# Adding a new instance family will require determining the correct productName for the query filter.
#   the -i or --instance switch will show all the productNames for a given instance
#   azure_pricing.py --instance <instance type>
azure_instances = [{'family': 'Las v3', 'query_string_ext': "and productName eq 'Lasv3 Series Linux'"
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
