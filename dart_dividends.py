#-*- coding:utf-8 -*-
# Parsing dividends data from DART
import urllib.request
import urllib.parse
import xlsxwriter
import os
import time
import sys
import getopt
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

def main():

	# Default
	config_mode = 0
	config_start_year	= 2017
	config_start_month	= 12
	config_start_day	= 15
	config_end_year		= 2017
	config_end_month	= 12
	config_end_day		= 15
	corp = "삼성전자"
	workbook_name = "DART_dividends.xlsx"

	try:
		opts, args = getopt.getopt(sys.argv[1:], "m:s:e:c:o:h", ["mode=", "start=", "end=", "corp=", "output", "help"])
	except getopt.GetoptError as err:
		print(err)
		sys.exit(2)
	for option, argument in opts:
		if option == "-h" or option == "--help":
			help_msg = """
================================================================================
-m or --mode <number>   :  Operation Mode
                            0 : Find posting of dividends in specific period
                            1 : Find all posting of dividends for specific corporation
-s or --start <number>  :  Start of period
                            year(4digits) + month(2digits) + day(2digits)
-e or --end <number>    :  End of period
                            year(4digits) + month(2digits) + day(2digits)
-c or --corp <name>     :  Corporation name
-o or --output <name>	:  Output file name
-h or --help            :  Show help messages

<Example>
>> python dart_dividends.py -m 0 -s 20171115 -e 20171215 -o out_file_name
>> python dart_dividends.py -m 1 -c S-Oil
================================================================================
					"""
			print(help_msg)
			sys.exit(2)
		elif option == "--mode" or option == "-m":
			config_mode = int(argument)
		elif option == "--start" or option == "-s":
			config_start_year	= int(argument[0:4])
			config_start_month	= int(argument[4:6])
			config_start_day	= int(argument[6:8])
		elif option == "--end" or option == "-e":
			config_end_year		= int(argument[0:4])
			config_end_month	= int(argument[4:6])
			config_end_day		= int(argument[6:8])
		elif option == "--corp" or option == "-c":
			corp = argument
		elif option == "--output" or option == "-o":
			workbook_name = argument + ".xlsx"

	# URL for Mode 0
	url_templete_0 = "http://dart.fss.or.kr/dsab002/search.ax?reportName=%s&&maxResults=100&&startDate=%s&&endDate=%s"
	# URL for Mode 1
	url_templete_1 = "http://dart.fss.or.kr/dsab002/search.ax?reportName=%s&&maxResults=100&&textCrpNm=%s"
	headers = {'Cookie':'DSAB002_MAXRESULTS=5000;'}
	
	dart_div_list = []

	#start_day = datetime(2017,11,15)
	#end_day = datetime(2017,12,15)
	start_day = datetime(config_start_year, config_start_month, config_start_day)
	end_day = datetime(config_end_year, config_end_month, config_end_day)
	delta = end_day - start_day

	# 배당
	report = "%EB%B0%B0%EB%8B%B9"

	for i in range(delta.days + 1):

		d = start_day + timedelta(days=i)
		rdate = d.strftime('%Y%m%d')
		print(rdate)
	
		if (config_mode == 0):
			handle = urllib.request.urlopen(url_templete_0 % (report, rdate, rdate))
		# config mode 1
		else:
			handle = urllib.request.urlopen(url_templete_1 % (report, urllib.parse.quote(corp)))
			print("URL" + url_templete_1 % (report, corp))

		data = handle.read()
		soup = BeautifulSoup(data, 'html.parser', from_encoding='utf-8')
		
		table = soup.find('table')
		trs = table.findAll('tr')
		tds = table.findAll('td')
		counts = len(tds)
		print(counts)

		#if counts > 0:
		if counts > 2:
			# Delay operation
			time.sleep(20)
		
			link_list = []
			docid_list = []
			date_list = []
			corp_list = []
			market_list = []
			title_list = []
			reporter_list = []
			tr_cnt = 0
			
			for tr in trs[1:]:
				tr_cnt = tr_cnt + 1
				time.sleep(1)
				tds = tr.findAll('td')
				link = 'http://dart.fss.or.kr' + tds[2].a['href']
				date = tds[4].text.strip().replace('.', '-')
				corp_name = tds[1].text.strip()
				market = tds[1].img['title']
				title = " ".join(tds[2].text.split())
				reporter = tds[3].text.strip()
				
				link_list.append(link)
				date_list.append(date)
				corp_list.append(corp_name)
				market_list.append(market)
				title_list.append(title)
				reporter_list.append(reporter)
				#print(corp_name)
				#print(title)

				if ((title == "[기재정정]현금ㆍ현물배당결정") or (title == "현금ㆍ현물배당결정") or (title=="현금배당결정") or (title == "분기ㆍ중간배당결정")) and (market != "코넥스시장"):
					dart_div_sublist = []

					print(corp_name)
					print(title)
					print(date)
					handle = urllib.request.urlopen(link)
					#print(link)
					data = handle.read()
					soup2 = BeautifulSoup(data, 'html.parser', from_encoding='utf-8')
					#print(soup2)

					test = soup2.find('a', {'href' : '#download'})['onclick']
					words = test.split("'")
					#print(words)
					rcpNo = words[1]
					dcmNo = words[3]
					#print(rcpNo)
					#print(dcmNo)

					dart2 = soup2.find_all(string=re.compile('dart2.dtd'))
					dart3 = soup2.find_all(string=re.compile('dart3.xsd'))
					year = int(date[0:4])

					if len(dart3) != 0:
						link2 = "http://dart.fss.or.kr/report/viewer.do?rcpNo=" + rcpNo + "&dcmNo=" + dcmNo + "&eleId=2&offset=4916&length=3668&dtd=dart3.xsd"
						#link2 = "http://dart.fss.or.kr/report/viewer.do?rcpNo=" + rcpNo + "&dcmNo=" + dcmNo + "&eleId=0&offset=0&length=0&dtd=dart3.xsd"
					elif (title == "분기ㆍ중간배당결정"):
						link2 = "http://dart.fss.or.kr/report/viewer.do?rcpNo=" + rcpNo + "&dcmNo=" + dcmNo + "&eleId=0&offset=0&length=0&dtd=dart2.dtd"
					elif len(dart2) != 0:
						if year < 2007:
							link2 = "http://dart.fss.or.kr/report/viewer.do?rcpNo=" + rcpNo + "&dcmNo=" + dcmNo + "&eleId=0&offset=0&length=0&dtd=dart2.dtd"
						else:
							link2 = "http://dart.fss.or.kr/report/viewer.do?rcpNo=" + rcpNo + "&dcmNo=" + dcmNo + "&eleId=87&offset=7601&length=4738&dtd=dart2.dtd"
					else:
						link2 = "http://dart.fss.or.kr/report/viewer.do?rcpNo=" + rcpNo + "&dcmNo=" + dcmNo + "&eleId=0&offset=0&length=0&dtd=HTML"  
					
					#print(link2)

					try:
						handle = urllib.request.urlopen(link2)
						#print(handle)
						data = handle.read()
						soup3 = BeautifulSoup(data, 'html.parser', from_encoding='utf-8')
						#print(soup3)

						tables = soup3.findAll("table")
						
						if len(tables) == 1 or len(tables) == 2:
							div_table = soup3.find("table")
						else:
							print("Tables", len(tables))
							#div_table = soup3.findAll("table")[2]
							div_table = soup3.findAll("table")[-1]
					
						# 최신 공시의 포맷
						# [0]   1. 배당구분
						# [1]   2. 배당종류
						# [2]   현물자산의 상세내역
						# [3]   3. 1주당 배당금(원) 보통주식
						# [4]   3. 1주당 배당금(원) 종류주식
						# [5]   차등배당 여부
						# [6]   4. 시가배당율(%) 보통주식 
						# [7]   4. 시가배당율(%) 종류주식
						# [8]   5. 배당금총액(원)
						# [9]   6. 배당기준일
						# [10]  7. 배당금지급 예정일자
						# [11]  8. 승인기관
						# [12]  9 . 주주총회 예정일자
						# [13]  10. 이사회결의일(결정일)
						div_trs = div_table.findAll('tr')
						#print(len(div_trs))
						if (title == "분기ㆍ중간배당결정"):
							if (len(div_trs) == 14) or (len(div_trs) == 15):
								div_cat = "분기배당"
								div_type = ""
								div_normal = div_trs[3].findAll('td')[2].text.strip()
								div_normal2 = div_trs[4].findAll('td')[1].text.strip()
								#div_ratio1 = div_trs[9].findAll('td')[1].text
								div_ratio1 = "0"
								div_ratio2 = "0"
							elif (len(div_trs) == 12):
								div_cat = "분기배당"
								div_type = ""
								div_normal = div_trs[1].findAll('td')[2].text.strip()
								div_normal2 = div_trs[2].findAll('td')[1].text.strip()
								div_ratio1 = "0"
								div_ratio2 = "0"
						else:
							if (len(div_trs) == 20):
								div_cat = div_trs[0].findAll('td')[1].text.strip()
								#print(div_cat)
								div_type = div_trs[1].findAll('td')[1].text.strip()
								#print(div_type)
								div_normal = div_trs[3].findAll('td')[2].text.strip()
								#print(div_normal)
								div_normal2 = div_trs[4].findAll('td')[1].text.strip()
								#print(div_normal2)
								div_ratio1 = div_trs[6].findAll('td')[2].text.strip()
								div_ratio2 = div_trs[7].findAll('td')[1].text.strip()
							elif (len(div_trs) == 18) or (len(div_trs) == 17):
								div_cat = div_trs[0].findAll('td')[1].text.strip()
								div_type = div_trs[1].findAll('td')[1].text.strip()
								div_normal = div_trs[3].findAll('td')[2].text.strip()
								div_normal2 = div_trs[4].findAll('td')[1].text.strip()
								div_ratio1 = div_trs[5].findAll('td')[2].text.strip()
								div_ratio2 = div_trs[6].findAll('td')[1].text.strip()
							elif (len(div_trs) == 14) or (len(div_trs) == 13):
								div_cat = div_trs[0].findAll('td')[1].text.strip()
								div_type = ""
								div_normal = div_trs[1].findAll('td')[2].text.strip()
								div_normal2 = div_trs[2].findAll('td')[1].text.strip()
								div_ratio1 = div_trs[3].findAll('td')[2].text.strip()
								div_ratio2 = div_trs[4].findAll('td')[1].text.strip()
							elif (len(div_trs) == 24) or (len(div_trs) == 26):
								if year == 2005 or year == 2006:
									div_cat = "결산배당"
									div_type = ""
									div_normal = div_trs[0].findAll('td')[2].text.strip()
									div_normal2 = div_trs[1].findAll('td')[1].text.strip()
									div_ratio1 = div_trs[2].findAll('td')[2].text.strip()
									div_ratio2 = div_trs[3].findAll('td')[1].text.strip()
								else:
									div_cat = "결산배당"
									div_type = ""
									div_normal = div_trs[3].findAll('td')[2].text.strip()
									div_normal2 = div_trs[4].findAll('td')[1].text.strip()
									div_ratio1 = div_trs[7].findAll('td')[2].text.strip()
									div_ratio2 = div_trs[8].findAll('td')[1].text.strip()
							else:
								div_cat = "PARSING ERROR"
								div_type = ""
								div_normal = "0"
								div_normal2 = "0"
								div_ratio1 = "0"
								div_ratio2 = "0"
					except:
						print ("URL ERROR")
						div_cat = "URL ERROR"
						div_type = ""
						div_normal = "0"
						div_normal2 = "0"
						div_ratio1 = "0"
						div_ratio2 = "0"
				
					dart_div_sublist.append(date)
					dart_div_sublist.append(corp_name)
					dart_div_sublist.append(market)
					dart_div_sublist.append(title)
					dart_div_sublist.append(link)
					dart_div_sublist.append(div_cat)
					dart_div_sublist.append(div_type)
					dart_div_sublist.append(div_normal)
					dart_div_sublist.append(div_normal2)
					dart_div_sublist.append(div_ratio1)
					dart_div_sublist.append(div_ratio2)
					
					dart_div_list.append(dart_div_sublist)
				
	cur_dir = os.getcwd()
	
	# Write an Excel file

	#workbook = xlsxwriter.Workbook(workbook_name)
	#if os.path.isfile(os.path.join(cur_dir, workbook_name)):
	#	os.remove(os.path.join(cur_dir, workbook_name))
	workbook = xlsxwriter.Workbook(workbook_name)

	worksheet_result = workbook.add_worksheet('result')
	filter_format = workbook.add_format({'bold':True,
										'fg_color': '#D7E4BC'
										})

	percent_format = workbook.add_format({'num_format': '0.00%'})

	roe_format = workbook.add_format({'bold':True,
									  'underline': True,
									  'num_format': '0.00%'})

	num_format = workbook.add_format({'num_format':'0.00'})
	num2_format = workbook.add_format({'num_format':'#,##0'})
	num3_format = workbook.add_format({'num_format':'#,##0.00',
									  'fg_color':'#FCE4D6'})

	worksheet_result.set_column('A:A', 10)
	worksheet_result.set_column('B:B', 15)
	worksheet_result.set_column('C:C', 15)
	worksheet_result.set_column('D:D', 20)
	worksheet_result.set_column('H:H', 15)
	worksheet_result.set_column('I:I', 15)
	worksheet_result.set_column('J:J', 15)
	worksheet_result.set_column('K:K', 15)


	worksheet_result.write(0, 0, "날짜", filter_format)
	worksheet_result.write(0, 1, "회사명", filter_format)
	worksheet_result.write(0, 2, "분류", filter_format)
	worksheet_result.write(0, 3, "제목", filter_format)
	worksheet_result.write(0, 4, "link", filter_format)
	worksheet_result.write(0, 5, "배당구분", filter_format)
	worksheet_result.write(0, 6, "배당종류", filter_format)
	worksheet_result.write(0, 7, "보통주 배당금", filter_format)
	worksheet_result.write(0, 8, "우선주 배당금", filter_format)
	worksheet_result.write(0, 9, "보통주 시가배당률", filter_format)
	worksheet_result.write(0, 10, "우선주 시가배당률", filter_format)

	for k in range(len(dart_div_list)):
		worksheet_result.write(k+1,0, dart_div_list[k][0])
		worksheet_result.write(k+1,1, dart_div_list[k][1])
		worksheet_result.write(k+1,2, dart_div_list[k][2])
		worksheet_result.write(k+1,3, dart_div_list[k][3])
		worksheet_result.write(k+1,4, dart_div_list[k][4])
		worksheet_result.write(k+1,5, dart_div_list[k][5])
		worksheet_result.write(k+1,6, dart_div_list[k][6])
		worksheet_result.write(k+1,7, dart_div_list[k][7])
		worksheet_result.write(k+1,8, dart_div_list[k][8])
		worksheet_result.write(k+1,9, dart_div_list[k][9])
		worksheet_result.write(k+1,10, dart_div_list[k][10])

	workbook.close()


# Main
if __name__ == "__main__":
	main()


