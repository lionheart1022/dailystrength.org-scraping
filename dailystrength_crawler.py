import urllib2
import datetime
from bs4 import BeautifulSoup
import time
import pytz
import csv, os, re, sys, json
from dateutil import parser

g_csvfilename = "dailystrength_result.csv"
g_log_file = "log.txt"
g_max_log_lines = 10000
g_idx_for_log = 0
g_old_AtoZ_no=0
g_old_topic_no=0
g_old_page_no=0
g_old_item_no=0
g_isfilevalid=False
g_statusfilename="status.txt"

def print_to_log(str_to_log):
    #write a log file
    print(str_to_log)
    global g_log_file, g_max_log_lines, g_idx_for_log
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    g_idx_for_log += 1
    fo = open(g_log_file, "a")
    try:
        #str_to_log += "----------log line cnt: %s" % g_idx_for_log
        str_to_log = str_to_log.encode("utf8", "ignore")
        fo.write( st + "\t: " + str_to_log + "\n" )
    except:
        pass
    fo.close()
    if g_idx_for_log >= g_max_log_lines:
        open(g_log_file, 'w').close()
        g_idx_for_log = 0

def escape_Quotes(str):
    return str.replace("\n", "")
    #return str.replace('"', '\\"').replace("'", "\\'")
    #return str.replace('"', '').replace("'", "")

def parse_DateString(str):
    dt = parser.parse(str.strip())
    #t_CommentDate = dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    #20140416
    #format = "%Y-%m-%d %H:%M:%S %Z"
    rtn = dt.strftime('%Y-%m-%d')
    return rtn

###
# This processes one topic.
###
def process_one_page(one_url, AtoZ_no, AtoZ_title, topic_no, condition_topic, page_no):
    global g_csvfilename, g_statusfilename
    global g_old_AtoZ_no, g_old_topic_no, g_old_page_no, g_old_item_no
    rtn = False
    print_to_log("Processing >>> %s, %s, topic_no:%s, page_no: %s, %s" % (str(AtoZ_no), AtoZ_title, topic_no, page_no, one_url))

    req = urllib2.Request(one_url)
    response = urllib2.urlopen(req, timeout = 50)
    result = response.read()
    t_soup = BeautifulSoup(result,'html5lib')

    t_tags = t_soup.findAll('tr',attrs={'class':['sectiontableentry2','sectiontableentry1']})

    t_as2 = t_soup.findAll('a', text="next >")
    if len(t_as2) > 0:
        rtn = True

    idx = 0
    for t_tag in t_tags:
        if AtoZ_no == g_old_AtoZ_no and topic_no == g_old_topic_no and page_no == g_old_page_no and idx < g_old_item_no:
            #already processed this item
            idx += 1
            continue

        t_URL_of_post = ""
        t_Date_of_post = ""
        t_Condition_topic = condition_topic
        t_Author = ""
        t_Text_of_main_post = ""
        t_Number_of_replies = ""
        t_Reply_text = ""

        Reply_text_arr = []
        Reply_date_arr = []
        Authors_arr = []

        t_tds = t_tag.findAll('td')
        try:
            pstr = ''.join(t_tds[3].findAll(text=True) ).replace('\r\n', ' ')
            pstr = escape_Quotes(pstr.strip())
            t_Author = pstr.strip()

            t_as = t_tds[1].findAll('a')
            t_url = "http://www.dailystrength.org%s" % (t_as[0].get("href"))
            t_URL_of_post  = t_url

            #get Number of replies
            pstr = ''.join(t_tds[2].findAll(text=True) ).replace('\r\n', ' ')
            t_Number_of_replies = int(pstr.strip())
        except:
            idx += 1
            continue

        #####################################################################################################
        #  now, process one post
        print_to_log("Processing >>> %s" % (t_url))
        #write status file
        fo = open(g_statusfilename, "wb")
        strtemp = "AtoZ_no=%s,topic_no=%s,page_no=%s,item_no=%s" % (AtoZ_no, topic_no,page_no,idx)
        fo.write( strtemp)
        fo.close()

        idx += 1

        # load the post page
        req2 = urllib2.Request(t_url)
        response2 = urllib2.urlopen(req2)
        result2 = response2.read()
        t_soup2 = BeautifulSoup(result2,'html5lib')

        t2_tables = t_soup2.findAll('table',{"class":["discussion_topic"]})
        try:
            t2_divs = t2_tables[0].findAll('div',{"class":["discussion_text"]})
            t2_spans3 = t2_divs[0].findAll('span',{"class":["graytext"]})
            # get Date of Post
            pstr = ''.join(t2_spans3[0].findAll(text=True) ).replace('\r\n', ' ')
            pstr = pstr.strip()
            pstr = pstr.replace("Posted on ", "")
            t_Date_of_post = parse_DateString(pstr[:8])

            # get Text of main_post
            pstr = ''.join(t2_divs[0].findAll(text=True) ).replace('\r\n', ' ')
            pstr = escape_Quotes(pstr.strip())
            t_Text_of_main_post = pstr
        except:
            pass

        if t_Number_of_replies > 0:
            #loop to get all replies
            loop_flag_for_reply = True
            idx_for_reply = 1
            t_url2 = ""
            while loop_flag_for_reply:
                t3_tables = t_soup2.findAll('table',{"class":["reply_table"]})
                t3_trs = t3_tables[0].findAll('tr')
                for t3_tr in t3_trs:
                    t3_ps = t3_tr.findAll('p',{"class":["username"]})
                    t3_spans = t3_tr.findAll('span',{"class":["graytext"]})
                    t3_divs = t3_tr.findAll('div',{"class":["discussion_text"]})
                    if len(t3_ps) > 0 and len(t3_spans) > 0 and len(t3_divs) > 0:
                        try:
                            pstr = ''.join(t3_ps[0].findAll(text=True) ).replace('\r\n', ' ')
                            pstr = escape_Quotes(pstr.strip())
                            Authors_arr.append(pstr)

                            pstr = ''.join(t3_spans[1].findAll(text=True) ).replace('\r\n', ' ')
                            pstr = pstr.strip().replace("\n"," ").replace("\t", " ")
                            pstr = parse_DateString(pstr[:8])
                            Reply_date_arr.append(pstr)

                            pstr = ''.join(t3_divs[0].findAll(text=True) ).replace('\r\n', ' ')
                            pstr = escape_Quotes(pstr.strip())
                            Reply_text_arr.append(pstr)
                        except:
                            continue
                        loop_flag_for_reply = True

                if len(t_url2) > 0:
                    print_to_log("Processing >>> loop for replies page: %s" % (t_url2))

                #find "Next" link
                t3_tables2 = t_soup2.findAll("table",{"class":["bottom_reply"]})
                try:
                    t3_as =t3_tables2[0].findAll('a', text="Next")
                    if len(t3_as) > 0:
                        loop_flag_for_reply = True
                    else:
                        loop_flag_for_reply = False
                except:
                    loop_flag_for_reply = False

                idx_for_reply += 1
                if loop_flag_for_reply:
                    #navigate to next reply page
                    t_url2 = "%s/page-%s" % (t_url, idx_for_reply)
                    req2 = urllib2.Request(t_url2)
                    response2 = urllib2.urlopen(req2)
                    result2 = response2.read()
                    t_soup2 = BeautifulSoup(result2,'html5lib')

            #build Reply text
            i = 0
            Reply_arr = []
            while i < len(Authors_arr):
                try:
                    #prepare for json
                    lst={}
                    lst['author'] = Authors_arr[i]
                    lst['date']= Reply_date_arr[i]
                    lst['text']= Reply_text_arr[i]
                    Reply_arr.append(lst)
                    #pstr = json.dumps(lst)
                    #pstr = "(%s; %s; %s)" % (lst['author'], lst['text'], lst['date'])
                    #if t_Reply_text == "":
                    #    t_Reply_text = "%s" % (pstr)
                    #else:
                    #    t_Reply_text = "%s, %s" % (t_Reply_text, pstr)
                except:
                    pass
                i += 1
            t_Reply_text = json.dumps(Reply_arr)

        #####################################################################################################
        #  now, store in csv file
        #TimeStamp
        timestamp = time.time()
        utc = datetime.datetime.utcfromtimestamp(timestamp)
        utc = pytz.utc.localize(utc)
        # Format string
        format = "%Y-%m-%d %H:%M:%S %Z"
        # Print UTC time
        t_TimeStamp = utc.strftime(format)

        #write to csv file
        fdWriter = csv.writer(open(g_csvfilename, 'ab'))
        fdWriter.writerow([t_URL_of_post.encode('utf8'),t_Date_of_post.encode('utf8'),t_Condition_topic.encode('utf8'),t_Author.encode('utf8'),
                           t_Text_of_main_post.encode('utf8'),t_Number_of_replies,t_Reply_text.encode('utf8'),t_TimeStamp])

    return rtn

###
# This processes one topic
###
def process_one_topic(one_url, AtoZ_no, AtoZ_title, topic_no, condition_topic):
    global g_csvfilename, g_statusfilename
    global g_old_AtoZ_no, g_old_topic_no, g_old_page_no, g_old_item_no

    loop_flag = True
    idx = 1
    while loop_flag:
        if g_old_AtoZ_no == AtoZ_no and topic_no == g_old_topic_no and idx < g_old_page_no:
            #already processed
            pass
        else:
            t_url = "%s/page-%s" % (one_url, idx)
            #print_to_log("Processing >>> %s, %s, %s, page_no: %s" % (str(AtoZ_no), AtoZ_title, one_url, idx))
            loop_flag = process_one_page(t_url, AtoZ_no, AtoZ_title, topic_no, condition_topic, idx)
        idx += 1
###
# This process one Alpha char
###
def process_one_AtoZ(one_url, AtoZ_title, AtoZ_no):
    global g_csvfilename, g_statusfilename
    global g_old_AtoZ_no, g_old_topic_no, g_old_page_no, g_old_item_no

    print_to_log("Processing >>> %s, %s, %s" % (str(AtoZ_no), AtoZ_title, one_url))

    #visit the page and get topics
    req = urllib2.Request(one_url)
    response = urllib2.urlopen(req)
    result = response.read()

    t_soup = BeautifulSoup(result,'html5lib')
    t_tags = t_soup.findAll('table',attrs={'class':'community_alpha_list'})
    t_h3s = None
    try:
        t_h3s = t_tags[0].findAll('h3')
    except:
        pass

    if t_h3s is not None:
        idx = 1
        for t_h3 in t_h3s:
            if g_old_AtoZ_no == AtoZ_no and idx < g_old_topic_no:
                #already processed
                pass
            else:
                t_as = t_h3.findAll('a')
                try:
                    t_url = t_as[0].get('href')
                    t_url = "http://www.dailystrength.org%s" % (t_url)
                    pstr = ''.join(t_as[0].findAll(text=True) ).replace('\r\n', ' ')
                    condition_topic = pstr.strip()

                    t_url = t_url.replace("support-group", "forum")
                    #process one topic
                    process_one_topic(t_url, AtoZ_no, AtoZ_title, idx, condition_topic)
                except:
                    pass
            idx += 1
    return

def main():
#    one_url = "http://www.medhelp.org/forums/Abuse-Support/show/147?page=1"
#    condition_topic = "Abuse-Support"
#    topic_no = 1
#    page_no = 1
#    process_one_page(one_url, condition_topic, topic_no, page_no)
#    return
    global g_csvfilename, g_statusfilename
    global g_old_AtoZ_no, g_old_topic_no, g_old_page_no, g_old_item_no
    global g_isfilevalid

    ### Staus file
    try:
        ins = open( g_statusfilename, "r" )
        for line in ins:
            p = re.compile(r'AtoZ_no=(?P<param>\d+),topic_no=(?P<param2>\d+),page_no=(?P<param3>\d+),item_no=(?P<param4>\d+)')
            m = p.search( line.rstrip() )
            if m is not None and m.group('param') is not None:
                g_old_AtoZ_no = int(m.group('param'))
                g_isfilevalid = True
                print_to_log("Last position - you scraped by this position.")
                print_to_log("before a-z-lnk no: "+str(g_old_AtoZ_no))
            if m is not None and m.group('param2') is not None:
                g_old_topic_no = int(m.group('param2'))
                g_isfilevalid = True
                print_to_log("before topic no: "+str(g_old_topic_no))
            if m is not None and m.group('param3') is not None:
                g_old_page_no = int(m.group('param3'))
                g_isfilevalid = True
                print_to_log("before page no: "+str(g_old_page_no))
            if m is not None and m.group('param4') is not None:
                g_old_item_no = int(m.group('param4'))
                g_isfilevalid = True
                print_to_log("before post_no: "+str(g_old_item_no))
    except:
        pass

    if g_isfilevalid == False:
    #already done or start from begin
        print_to_log("===============================================================================")
        print_to_log("<"+g_statusfilename+"> file stands for saving scraping staus. Don't touch this file!")
        print_to_log("Saving status into this file, scraper continues from the last position.")
        print_to_log("In the case when scraper is terminated unsuccessfully, scraper continues from the position in the next time.")
        #var = raw_input("Are you going to start scraping from begin?(yes/no):")
    	#if var.lower() != "yes" and var.lower() != "y":
        #    sys.exit()
        #var = raw_input("Did you backup all csv file?(yes/no):")
    	#if var.lower() != "yes" and var.lower() != "y":
        #    sys.exit()
            #remove all csv files
        #if os.path.exists(g_csvfilename):
        #    os.remove(g_csvfilename)

    #Start Crawler
    print_to_log("===================================================================================")
    print_to_log("scraping running...")
    #print(g_seeds)

    if not os.path.exists(g_csvfilename):
        with open(g_csvfilename,'wb') as f:
            fdWriter = csv.writer(f)
            fdWriter.writerow(['URL of post','Date of post','Condition topic','Author','Text of main_post', 'Number of replies', 'Reply text', 'TimeStamp'])
            print_to_log(g_csvfilename+" newly created!")

    ####
    # open "http://www.medhelp.org/forums/list" page and get all topic links
    one_url = "http://www.dailystrength.org/support-groups"
    req = urllib2.Request(one_url)
    response = urllib2.urlopen(req)
    result = response.read()

    t_soup = BeautifulSoup(result,'html5lib')
    t_tags = t_soup.findAll('div',attrs={'class':'a_to_z_narrow'})
    try:
        t_as = t_tags[0].findAll('a')
    except:
        t_as = None

    if t_as is not None:
        idx = 1
        for t_a in t_as :
            if idx < g_old_AtoZ_no:
                #already processed this topic before
                pass
            else:
                t_url = "http://www.dailystrength.org%s" % (t_a.get("href"))
                pstr = ''.join(t_a.findAll(text=True) ).replace('\r\n', ' ')
                t_AtoZ_title = pstr.strip()
                #print t_condition_topic
                #print t_url

                process_one_AtoZ(t_url, t_AtoZ_title, idx)
            idx += 1

    #done successfully!
    print_to_log("===================================================================================")
    print_to_log("Congratulations! Scraping successfully finished!")
    print_to_log("===================================================================================")
    #os.remove(g_statusfilename)

if __name__ == "__main__":
    #is being run directly
   main()