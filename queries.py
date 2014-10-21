list = {

'global':("select round(sum(totals.bounces)/count(*), 2) as bouncerate, round(avg(totals.pageviews)) as avgpageviews, "
                   "count(distinct(fullVisitorId)) as visitors, sum(totals.visits) as visits "
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "),

'by_date':("select date as date, sum(totals.visits) as visits, count(distinct(fullVisitorId)) as visitors "
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by date"),
               
'by_medium':("select trafficSource.medium as medium, sum(totals.visits) as visits, count(distinct(fullVisitorId)) as visitors, "
                   "round(sum(totals.bounces)/count(*), 2) as bouncerate, "
                   "round(avg(totals.pageviews)) as avgpageviews, round(avg(totals.timeOnSite)) as avgtimeonsite "
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by trafficSource.medium"),
        
'by_device':("select device.deviceCategory as device, sum(totals.visits) as visits "
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by device.deviceCategory"),
        
'by_browser':("select device.browser as browser, sum(totals.visits) as visits "
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by device.browser"),

'by_title':("select hits.page.pageTitle as pagetitle, count(hits.eventInfo.eventCategory) as eventcat, sum(totals.pageviews) as sumpageviews "
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where lower(trafficSource.referralPath) contains '%s' %s "
                   "group by hits.page.pageTitle"),

'by_model':("select customDimensions.value as model, sum(totals.pageviews) as sumpageviews "
                   "from %s "
                   #"where trafficSource.medium = 'organic' "
                   "where customDimensions.index = 9 "
                   "and lower(trafficSource.referralPath) contains '%s' %s "
                   "group by customDimensions.value "
                   "order by sumpageviews desc "
                   "limit 20")
                        
}
 