#! /usr/bin/python

import datetime
import numpy
import pandas.io.data
import feedparser
import urllib2
import collections
from bs4 import BeautifulSoup
import pickle
import sentiment_analysis_py.sentiment_analysis as sa
import re
import os

def pull_6_months(sym):
    start = (datetime.datetime.today() - datetime.timedelta(6*365/12))
    start = datetime.datetime(start.year, start.month, start.day)
    end = datetime.date.today()
    end = datetime.datetime(end.year, end.month, end.day)

    return pandas.io.data.DataReader(sym, 'google', start, end)

def pull_google_rss(sym):
    rss_feed = 'https://www.google.com/finance/company_news?q=NASDAQ:%s&ei=9M4FVtinBc62iALx7I2IAw&output=rss'
    return feedparser.parse(rss_feed % sym)

def print_list_feeds(sym):
    rss = pull_google_rss(sym)
    for x in range(len(rss.entries)):
        print str(x) + ':  ' + rss.entries[x].title + '   --   ' + rss.entries[x].published
    
def get_textbody_from_link(link):
    page_style_text =  {
            'www.fool.com' : ('span', {'class':'article-content'}),
            'www.bidnessetc.com' : ('div', {'class':'col-xs-24 article-content ads'}),
            'www.ibtimes.com' : ('div', {'class':'article-content'}),
            'www.valuewalk.com' : ('div', {'class':'entry-content'}),
            #'www.bloomberg.com' : ('div', {'class':'article-body__content'}), #not working all the way still grabs alot of other crap
            'investorplace.com' : ('div', {'class':'entry-content'}), #also lots of dumb formatting
            'www.bidnessetc.com' : ('div', {'class':'col-xs-24 article-content ads'}),
            'www.reuters.com' : ('span', {'id':'articleText'}),
            'learnbonds.com' : ('div', {'class':'entry-content'}),
            'www.technewstoday.com' : ('div', {'class':'article-details load'}),
            'www.foxbusiness.com' : ('div', {'itemprop':'articleBody'}),
            'newswatchinternational.com' : ('div', {'class':'td-post-content td-pb-padding-side'}), #alot of formatting flags
            'seekingalpha.com': ('div', {'id':'article_body'}),
            #'streetwisereport.com': ('div', {'class':'article-post-content'}),
            #'www.moneyflowindex.org': ('div', {'class':'entry-content'}),
            'www.smarteranalyst.com': ('div', {'class':'post-content clearfix'}),
            'www.wsobserver.com': ('div', {'class':'td-post-content'}),
                       } 

    #tags = soup.find_all('span', {'itemprop':'articleBody'})
    for key in page_style_text.keys():
        if key in link:
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib2.Request(link, None, headers)
            pageString = urllib2.urlopen(req, timeout=5).read()
            soup = BeautifulSoup(pageString, 'html5lib')
            text_body = page_style_text[key]
            tags = soup.find_all(text_body[0], text_body[1])
            text = [t.get_text() for t in tags]
            #print str(len(text))+' posts were found'
            #print text[0].encode('ascii', 'ignore')
            if text:
                return text[0].encode('ascii', 'ignore')
    with open('link_ni_page_style.txt', 'w') as fout:
        print >> fout, link

def analyze_canned_files():
    path = '/Users/Dallin/sync/fall2015/intelligent_systems_5600/pra/aapl_reports'
    from os import listdir
    from os.path import isfile, join
    onlyfiles = [ f for f in listdir(path) if isfile(join(path,f)) ]
    #print onlyfiles

    file_to_content = collections.OrderedDict()

    for filename in onlyfiles:
        with open(join(path,filename), 'r') as fin:
            content = fin.read().decode('utf-8').strip()
            file_to_content[filename] = content.encode('ascii', 'ignore')

    return file_to_content

def compute_avg_val(data_slice, index):
    #print data_slice
    #print data_slice.describe()
    #print data_slice.describe().loc['mean']
    #print data_slice.describe().loc['mean'].loc[index]
    return data_slice.describe().loc['mean'].loc[index]

def net_pos_neg(date, hist_data):
    ''' Look at 3 days before and 3 days after and date of interest
        average stocks on either side of day. return 1 for pos return 
        0 for neg '''
    split_fields = date.split('-')
    interest_date = datetime.date(int(split_fields[0]), int(split_fields[1]), int(split_fields[2]))
    low = (interest_date - datetime.timedelta(5))
    #print low
    high = (interest_date + datetime.timedelta(5))
    #print high
    data_slice = hist_data[str(low):str(high)]
    #print data_slice
    #print compute_avg_val(hist_data[str(low):str(date)], 'Close')
    #print compute_avg_val(hist_data[str(date):str(high)], 'Close')
    return 0 if compute_avg_val(hist_data[str(low):str(date)], 'Close') > compute_avg_val(hist_data[str(date):str(high)], 'Close') else 1
    
def split_training_set(print_files=0):
    canned_files = analyze_canned_files()
    dates = set()
    for file_name in canned_files.keys():
        dates.add(file_name.split('.')[0] if '_' not in file_name else file_name.split('_')[0])

    val_2_date = collections.OrderedDict()
    val_2_date['pos'] = []
    val_2_date['neg'] = []
    
    for date in sorted(dates):
        if net_pos_neg(date, hist_data):
            val_2_date['pos'].append(date)
        else:
            val_2_date['neg'].append(date)
    # print two files -- pos and neg
    # 

    pos_content = []
    neg_content = []
    
    for pos_date in val_2_date['pos']:
        for file_name in canned_files.keys():
            if pos_date in file_name:
                #print 'Pos: ', pos_date, file_name
                pos_content.append(canned_files[file_name])
    for neg_date in val_2_date['neg']:
        for file_name in canned_files.keys():
            if neg_date in file_name:
                #print 'Neg: ', neg_date, file_name
                neg_content.append(canned_files[file_name])
    if print_files:
        with open('pos_train_content.txt', 'w') as fout:
            for content in pos_content:
                print >> fout, content
        with open('neg_train_content.txt', 'w') as fout:
            for content in neg_content:
                print >> fout, content
    return val_2_date
    
def eval_sentiment(text):
    classifier = None
    best_words = None
    with open('classifier.pickle', 'r') as fout:
        (classifier, best_words) = pickle.load(fout)
    features = sa.create_feature(text, sa.best_word_features, best_words)
    return sa.check_features(features,classifier)

def update_training_files_filter(running_data):
    five_days_ago = (datetime.date.today() - datetime.timedelta(5))
    for day in running_data: #inefficient
        for sym in running_data[day]:
            hist_data = pull_6_months(sym)
            if(net_pos_neg(day, hist_data)):
                for article in [x for x in running_data[day][sym] if x != 'overall_pred' and x != 'overall_analyzed']:
                    running_data[day][sym][article]['actual'] = 'pos'
                    if 'added_2_filter' not in running_data[day][sym][article]:
                        running_data[day][sym][article]['added_2_filter'] = 0
                    if day < str(five_days_ago) and not running_data[day][sym][article]['added_2_filter']:
                        with open('sentiment_analysis_py/training_data/pos_train_content.txt', 'a') as fout:
                            print >> fout, running_data[day][sym][article]['text']
                            running_data[day][sym][article]['added_2_filter'] = 1
                            print "AddedP: " + str(day) + " " + str(sym) + " " + str(article)
            else:
                for article in [x for x in running_data[day][sym] if x != 'overall_pred' and x != 'overall_analyzed']:
                    running_data[day][sym][article]['actual'] = 'neg'
                    if 'added_2_filter' not in running_data[day][sym][article]:
                        running_data[day][sym][article]['added_2_filter'] = 0
                    if day < str(five_days_ago) and not running_data[day][sym][article]['added_2_filter']:
                        with open('sentiment_analysis_py/training_data/neg_train_content.txt', 'a') as fout:
                            print >> fout, running_data[day][sym][article]['text']
                            running_data[day][sym][article]['added_2_filter'] = 1
                            print "AddedN: " + str(day) + " " + str(sym) + " " + str(article)
                            
def article_ratings(running_data, day, sym):
    pos = 0
    neg = 0
    for article in [x for x in running_data[day][sym] if x != 'overall_pred' and x != 'overall_analyzed']:
        if running_data[day][sym][article]['prediction'] == 'pos':
            pos = pos + 1
        else:
            neg = neg + 1
    return (pos, neg)

def report_data():
    running_data = None
    with open('running_data.pickle', 'r') as fout:
        running_data = pickle.load(fout)
    #print [x for x in running_data] 
    sym_2_data = {}
    c_vs_n_2_day = {}
    for day in sorted(running_data):
        for sym in running_data[day]:
            if sym not in sym_2_data:
                sym_2_data[sym] = []
            #print 'day: ' +str(day) + ' sym: ' + str(sym) + ' -- ' + str(running_data[day][sym]['overall_pred']) + ' -- ' + str(running_data[day][sym]['overall_analyzed'])
            (num_pos, num_neg) = article_ratings(running_data, day, sym)
            actual = None
            for article in [x for x in running_data[day][sym] if x != 'overall_pred' and x != 'overall_analyzed']:
                actual = running_data[day][sym][article]['actual']
            sym_2_data[sym].append((num_pos, num_neg, day, str(running_data[day][sym]['overall_pred']), actual))
    #TODO: Split into pos/neg day
    with open('data_reports/p_vs_n/allpoints_p.txt', 'w') as fout_comb_p:
        with open('data_reports/p_vs_n/allpoints_n.txt', 'w') as fout_comb_n:
            for sym in sorted(sym_2_data):
                with open('data_reports/p_vs_n/' + str(sym) + '_p.txt', 'w') as fout_p:
                    with open('data_reports/p_vs_n/' + str(sym) + '_n.txt', 'w') as fout_n:
                        for rec in sym_2_data[sym]:
                            if int(rec[3]) >= 0: 
                                print >> fout_comb_p, str(rec[0]) + ' ' + str(rec[1]) + ' ' + str(sym) + str(rec[2][2:])
                                print >> fout_p, str(rec[0]) + ' ' + str(rec[1]) + ' ' + str(sym) + str(rec[2][2:])
                            else:
                                print >> fout_comb_n, str(rec[0]) + ' ' + str(rec[1]) + ' ' + str(sym) + str(rec[2][2:])
                                print >> fout_n, str(rec[0]) + ' ' + str(rec[1]) + ' ' + str(sym) + str(rec[2][2:])
    with open('data_reports/c_vs_i/allpoints_p.txt', 'w') as fout_comb_p:
        with open('data_reports/c_vs_i/allpoints_n.txt', 'w') as fout_comb_n:
            for sym in sorted(sym_2_data):
                with open('data_reports/c_vs_i/' + str(sym) + '_p.txt', 'w') as fout_p:
                    with open('data_reports/c_vs_i/' + str(sym) + '_n.txt', 'w') as fout_n:
                        for rec in sym_2_data[sym]:
                            if int(rec[3]) >= 0 and rec[4] == 'pos' or int(rec[3]) < 0 and rec[4] == 'neg': 
                                print >> fout_comb_p, rec[3] + " " + str(sym) + str(rec[2][2:])
                                print >> fout_p, rec[3] + " " + str(sym) + str(rec[2][2:])
                            else:
                                if rec[4]:
                                    print >> fout_comb_n, rec[3] + " " + str(sym) + str(rec[2][2:])
                                    print >> fout_n, rec[3] + " " + str(sym) + str(rec[2][2:])

if __name__ == '__main__':
    symbols = ['AAPL','MU', 'MSFT', 'GOOG', 'NVDA', 'AMD', 'INTC', 'ORCL', 'ADBE', 'TXN']
    running_data = {}
    if os.path.exists('running_data.pickle'):
        with open('running_data.pickle', 'r') as fout:
            running_data = pickle.load(fout)
    today = datetime.date.today()
    running_data[str(today)] = {}
    for sym in symbols:
        running_data[str(today)][sym] = {}
        #print_list_feeds(sym)
        d = pull_google_rss(sym)
        articles_analyzed = 0
        overall_pred_today = 0
        pattern = r''+ str(today.day) + ' \w\w\w ' + str(today.year)
        date_match = re.compile(pattern)
        for x in range(len(d.entries)):
            #print d.entries[x].link
            text = get_textbody_from_link(d.entries[x].link)
            if text and date_match.search(d.entries[x].published):
                articles_analyzed = articles_analyzed + 1
                running_data[str(today)][sym][x] = {}
                running_data[str(today)][sym][x]['title'] = d.entries[x].title
                running_data[str(today)][sym][x]['text'] = text
                prediction = eval_sentiment(text)
                overall_pred_today = overall_pred_today + 1 if prediction == 'pos' else overall_pred_today - 1
                running_data[str(today)][sym][x]['prediction'] = prediction
                running_data[str(today)][sym][x]['actual'] = None
                #print eval_sentiment(text)

        running_data[str(today)][sym]['overall_pred'] = overall_pred_today
        running_data[str(today)][sym]['overall_analyzed'] = articles_analyzed
        print sym + ' -- ' + str(today) + ' -- Score: ' + str(overall_pred_today) + ' -- Analyzed: ' + str(articles_analyzed)

    update_training_files_filter(running_data)
    
    #print running_data
    with open('running_data.pickle', 'w') as fout:
        pickle.dump(running_data, fout)

    report_data()
