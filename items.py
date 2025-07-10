import scrapy


# Nested Items can be used
class BayutAgencyItem(scrapy.Item):
    agency_url = scrapy.Field()
    agency_name = scrapy.Field()
    num_of_properties = scrapy.Field()
    about_agency = scrapy.Field()
    agents = scrapy.Field()
