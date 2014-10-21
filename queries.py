list = {

'global':("select sum(totals.bounces)/count(*) as bouncerate, avg(totals.pageviews) as avgpageviews, "
                   "count(distinct(fullVisitorId)) as visitors, sum(totals.visits) as visits"
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "),

'by_date':("select sum(totals.visits) as visits, count(distinct(fullVisitorId)) as visitors, "
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by date"),
               
'by_medium':("select sum(totals.visits) as visits, count(distinct(fullVisitorId)) as visitors, "
                   "sum(totals.bounces)/count(*) as bouncerate, "
                   "avg(totals.pageviews) as avgpageviews, avg(totals.timeOnSite) avgtimeonsite"
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by trafficSource.medium"),
        
'by_device':("select sum(totals.visits) as visits"
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by device.deviceCategory"),
        
'by_browser':("select sum(totals.visits) as visits"
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by device.browser"),

'by_title':("select count(hits.eventInfo.eventCategory) as eventcat, sum(totals.pageviews) as sumpageviews"
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by hits.page.pageTitle"),

'by_model':("select customDimensions.value, sum(totals.pageviews) as sumpageviews "
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where customDimensions.index = 9 "
                   "and lower(trafficSource.referralPath) contains '%s' %s "
                   "group by customDimensions.value "
                   "order by sumpageviews desc "
                   "limit 20")
                        
}
 