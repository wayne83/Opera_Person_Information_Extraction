import requests
import re 
import urllib
import requests.exceptions as RequestException
from xml.dom import minidom
import os
from lxml import etree

#访问URL，获取URl的html文件
def get_url_html(url,index):
	hds=[{'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'},
		 {'User-Agent':'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'},
		 {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'}]

	r = requests.get(url,headers=hds[index%len(hds)])
	try:
		if r.status_code == 200:
			return r.text
		else:
			return None
	except RequestException:
		return None

#使用reStr去匹配获取的html，提取页面信息
def get_detail_url(html,reStr):
	pattern = re.compile(reStr,re.S)

	items = re.findall(pattern,html)
	print("人物网站数目为：" + str(len(items)))
	for item in items:
		yield item

#将获取的数据以xml格式写入
def write_msg(content,url):

	#新建xml文档对象
	xml = minidom.Document()
	if os.path.isfile(url):
		print("True")
		write_to_xml(content,xml,url)
	else:
		print("False")
		#创建第一个节点,第一个节点就是根节点
		root = etree.Element("root",nsmap={'xsi': 'http://b.c/d'})
		tree = etree.ElementTree(root)
		tree.write(url, pretty_print=True, xml_declaration=True, encoding='utf-8')
		#写入第一个数据
		write_to_xml(content,xml,url)

def write_to_xml(content,xml,url):

	#打开文档，使用parse方法解析
	xml = etree.parse(url)

	#获取根节点
	root = xml.getroot()

	node = {}
	#创造子节点
	Performers_node = etree.SubElement(root,"Performers")
	Performers_node.set("name",content["name"])

	#为子节点加入文本
	for key,value in content.items():
		node[key] = etree.SubElement(Performers_node,key)
		node[key].text = str(value)

	#保存文档
	tree = etree.ElementTree(root)  
	tree.write(url, pretty_print=True, xml_declaration=True, encoding='utf-8')

#使用reStr匹配人物详细信息页面的html，获取www.jingju.com的人物详细信息
def get_Jingju_detail_msg(url,html,reStr,num):
	pattern = re.compile(reStr,re.S)

	items = re.findall(pattern,html)
	print("详细信息页面爬取 --------------->" + str(len(items)))
	for item in items:
		sub_pattern = [re.compile("(<span.*?>)",re.S),re.compile("(<a.*?>)",re.S),re.compile("(</span>)"),re.compile("(</a>)"),re.compile("(<br />)"),
			re.compile("(&\w+;)",re.S),re.compile("(\\r)"),re.compile("(\\n)"),re.compile("(<.*?>)")]

		detail_msg = item[6].replace(" ","")

		for i in range(len(sub_pattern)):
			detail_msg = sub_pattern[i].sub("",detail_msg)

		detail_msg = detail_msg.strip()

		yield {
			"Index":str(num+1),
			"源网址":url,
			"name":item[0],
			"性别":item[2],
			"行当":item[3],
			"常演剧目":item[5],
			"详细资料":detail_msg
		}

#爬取www.jingju.com页面
def getJingJu(index,total,saveurl):
	global num
	if index == 1:
		url = "http://www.jingju.com/jingjurenwu/yuantuanmingjia/index.html"
	else:
		url = "http://www.jingju.com/jingjurenwu/yuantuanmingjia/index_" + str(index) +".html"

	print("\n正在爬取" + "第" + str(index) + "页内容 --------------->\n")

	people_html = get_url_html(url,index)
	re_detail_url = "<div class=\"RWlist\">.*?<dd class=\"che\"><a href=\"(.*?)\".*?</dd>"

	for detail_url in get_detail_url(people_html,re_detail_url):
		detail_url = "http://www.jingju.com" + detail_url

		if num >= total:
			break
		print("num:" + str(num) + " total:" + str(total) )
		detail_msg_html = get_url_html(detail_url,index)
		re_detail_msg = ("<div class=\"Rnamer\">.*?<p>.*?</label>(.*?)</p>.*?<p>.*?</label>(.*?)</p>.*?<p>.*?</label>(.*?)</p>"
		+ ".*?<p>.*?</label>(.*?)</p>.*?<p>.*?</label>(.*?)</p>.*?<p>.*?</label>(.*?)</p>"
		+ ".*?<p class=\"jianjie\">.*?</label>(.*?)</p>")

		for item in get_Jingju_detail_msg(detail_url,detail_msg_html,re_detail_msg,num):
			num += 1
			write_msg(item,saveurl)
			#print(item)

#爬取www.xikao.com中的内容
def getXikao(total,saveurl):
	global num 
	arr_genre = ["生行演员","旦行演员","净行演员","丑行演员"]
	preurl = "http://history.xikao.com/directory/" + urllib.parse.quote("京剧") + "/" 
	for i in range(len(arr_genre)):
		url = preurl + urllib.parse.quote(arr_genre[i])
		person_cate_html = get_url_html(url,i)

		#获取人物详情页面Url的正则匹配
		reStr = ("<li class=\"bullet\">.*?<a href=\"(.*?)\" class.*?>.*?(<span class=\"brief_info\">(.*?)</span>.*?)?</li>")
		for detail_item in get_detail_url(person_cate_html,reStr):
			if num >= total:
				break
			print("\n正在爬取" + "第" + str(num+1) + "个人物 --------------->\n")
			#人物详情页面Url
			detail_url =  "http://history.xikao.com" + detail_item[0]
			birth_death_time = detail_item[2].replace("(","")
			birth_death_time = birth_death_time.replace(")","").split("-")
			birth = ""
			death = ""
			if len(birth_death_time) == 2:
				birth = birth_death_time[0]
				death = birth_death_time[1]

			re_detailStr = ("<div class=\"namecard\">.*?</div>.*?</div>.*?<b>(.*?)</b>(.*?)<br />(.*?)<hr size=\"1\".*?</td>")
			detail_msg_html = get_url_html(detail_url,num)
			item = get_xikao_detail_msg(detail_msg_html,re_detailStr)
			num+=1
			try:
				content = {
					"Index":num,
					"Url":urllib.parse.unquote(detail_url),
					"name":item["name"],
					"sex":item["sex"],
					"genre":arr_genre[i],
					"birthdate":birth,
					"deathdate":death,
					"details":item["detail_msg"],
					"person_msg":item["person_msg"]
				}
				write_msg(content,saveurl)
			except Exception:
				print("Content设置出错!")

#获取人物详细页面的信息
def get_xikao_detail_msg(html,reStr):

	pattern = re.compile(reStr,re.S)
	items = re.findall(pattern,str(html))
	print("详细信息页面爬取 --------------->" + str(len(items)))

	for item in items:
		#处理长文本中遗留的html元素
		sub_pattern = [re.compile("(<span.*?>)",re.S),re.compile("(<a.*?>)",re.S),re.compile("(</span>)"),re.compile("(</a>)"),re.compile("(<br />)"),
			re.compile("(&\w+;)",re.S),re.compile("(\\r)"),re.compile("(\\n)"),re.compile("(<.*?>)")]
		detail_msg = item[2].replace(" ","")
		person_msg = item[1][1:]

		for i in range(len(sub_pattern)):
			detail_msg = sub_pattern[i].sub("",detail_msg)
		for i in range(len(sub_pattern)):
			person_msg = sub_pattern[i].sub("",person_msg)

		sexStr = item[1]
		sex = ""
		for i in range(len(item[1])):
			if sexStr[i] == "男" or sexStr[i] == "女":
				sex = sexStr[i]
		name = item[0] 
		return {
			"person_msg":person_msg,
			"detail_msg":detail_msg,
			"name":name,
			"sex":sex
		}


if __name__ == '__main__':
	print("开始")
	global num 
	num = 0
	total = 2000

	#需要爬取的数据量
	total = int(input("请输入需要爬取的数据量"))
	#需要保存的文件名
	savefilename = input("请输入需要保存的文件名")
	#爬取网站选择
	crawlerWeb = input("请选择需要爬取的网站：1.www.xikao.com(数据量充足) 2.www.jingju.com(数据量只有500条)")

	if savefilename.replace(" ","'") != "":
		saveurl = "../Information/" + savefilename + ".xml"
	else:	
		if crawlerWeb == "1":
			saveurl = "../Information/Opera_character_by_Xikao.xml"
		else:
			saveurl = "../Information/Opera_character_by_JingJu.xml"
	if crawlerWeb == "1":
		#爬取www.xikao.com网站的京剧名家
		getXikao(total,saveurl)
	elif crawlerWeb == "2":
		#爬取www.jingju.com网站的京剧名家(只有500+数据)
		for i in range(1,85):
			if num >= total:
				break
			else:
				getJingJu(i,total,saveurl)
	else:
		print("输入错误，请重新输入")
	

