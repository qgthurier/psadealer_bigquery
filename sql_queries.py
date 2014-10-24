easy = {

'global':("select round(sum(totals.bounces)/count(*), 2) as bouncerate, round(avg(totals.pageviews)) as avgpageviews, "
                   "count(distinct(fullVisitorId)) as visitors, sum(totals.visits) as visits "
                   "from (TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('%s'), TIMESTAMP('%s'))) "
                   "where lower(trafficSource.referralPath) contains '%s'"),

'by_date':("select date as date, sum(totals.visits) as visits, count(distinct(fullVisitorId)) as visitors "
                   "from (TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('%s'), TIMESTAMP('%s'))) "
                   "where lower(trafficSource.referralPath) contains '%s'"),
               
'by_medium':("select trafficSource.medium as medium, sum(totals.visits) as visits, count(distinct(fullVisitorId)) as visitors, "
                   "round(sum(totals.bounces)/count(*), 2) as bouncerate, "
                   "round(avg(totals.pageviews)) as avgpageviews, round(avg(totals.timeOnSite)) as avgtimeonsite "
                   "from (TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('%s'), TIMESTAMP('%s'))) "
                   "where lower(trafficSource.referralPath) contains '%s' "
                   "group by medium"),
        
'by_device':("select device.deviceCategory as device, sum(totals.visits) as visits "
                   "from (TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('%s'), TIMESTAMP('%s'))) " 
                   "where lower(trafficSource.referralPath) contains '%s' "
                   "group by device"),
        
'by_browser':("select device.browser as browser, sum(totals.visits) as visits "
                   "from (TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('%s'), TIMESTAMP('%s'))) "
                   "where lower(trafficSource.referralPath) contains '%s' " 
                   "group by browser"),

'by_title':("select count(hits.eventInfo.eventCategory) as eventcat, sum(totals.pageviews) as sumpageviews, hits.page.pageTitle as pagetitle "
                   "from (TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('%s'), TIMESTAMP('%s'))) "
                   "where lower(trafficSource.referralPath) contains '%s' " 
                   "group by pageTitle"),

'by_model':("select customDimensions.value as model, sum(totals.pageviews) as sumpageviews "
                   "from (TABLE_DATE_RANGE([87581422.ga_sessions_], TIMESTAMP('%s'), TIMESTAMP('%s'))) "
                   "where customDimensions.index = 9 "
                   "and lower(trafficSource.referralPath) contains '%s' "
                   "group by model "
                   "order by sumpageviews desc "
                   "limit 20")
                        
}

