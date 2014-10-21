list = {

'global':("select sum(totals.bounces)/count(*), avg(totals.pageviews), "
                   "count(distinct(fullVisitorId)), sum(totals.visits) "
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s "),

'by_date':("select sum(totals.visits), count(distinct(fullVisitorId)), "
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s "
                   "group by date"),
               
'by_medium':("select sum(totals.visits), count(distinct(fullVisitorId)), "
                   "sum(totals.bounces)/count(*), "
                   "avg(totals.pageviews), avg(totals.timeOnSite) "
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s "
                   "group by trafficSource.medium"),
        
'by_device':("select sum(totals.visits) "
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s "
                   "group by device.deviceCategory"),
        
'by_browser':("select sum(totals.visits) "
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s "
                   "group by device.browser"),

'by_title':("select count(hits.eventInfo.eventCategory), sum(totals.pageviews) "
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s "
                   "group by hits.page.pageTitle"),

'by_model':("select hits.customDimensions.9, sum(totals.pageviews) as tot "
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s "
                   "group by hits.customDimensions.9 "
                   "order by tot desc "
                   "limit 20")
                        
}
 