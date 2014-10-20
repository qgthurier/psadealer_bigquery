list = {
        
'visites':("select sum(totals.visits) as val,"
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s"),

'visitors':("select count(distinct(fullVisitorId)) as val,"
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s"),

'pageviews':("select avg(totals.pageviews) as val,"
                    "from %s "
                    "where trafficSource.medium = 'organic'"
                    "and lower(trafficSource.referralPath) contains '%s' %s"),

'bouncerate':("select sum(totals.bounces)/count(*) as val,"
                   "from %s "
                   "where trafficSource.medium = 'organic' "
                   "and lower(trafficSource.referralPath) contains '%s' %s")
        
}