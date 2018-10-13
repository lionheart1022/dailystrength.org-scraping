# dailystrength_crawler
There are several files for this scraper.

1) Install Python2.7

2) Python Modules(requirements.txt)
-In requirements.txt, there are modules which I used for this program.
-You should install those modules first.
-Open terminal and enter commands like this:

$cd <the path of this directory>
$sudo pip install -r requirements.txt

3) You can run "dailystrength_crawler.py" file on console.This is just a program file.

$cd <the path of this directory>
$python ./dailystrength_crawler.py

4) There is "log.txt" file and you can view the log.
5) "status.txt" file stands for saving scraping staus. Don't touch this file!
   Saving status into this file, scraper continues from the last position.
   In the case when scraper is terminated unsuccessfully, scraper continues from the position in the next time.
6) This crawler stores data in "dailystrength_result.csv" file. I attached a result file which I got on my side.
