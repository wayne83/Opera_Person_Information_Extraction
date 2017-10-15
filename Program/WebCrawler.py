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
	if os.path.isfile(url):
		print("True")
		write_to_xml(content,url)
	else:
		print("False")
		#创建第一个节点,第一个节点就是根节点
		root = etree.Element("root",nsmap={'xsi': 'http://b.c/d'})
		tree = etree.ElementTree(root)
		tree.write(url,pretty_print=True,xml_declaration=True, encoding='utf-8')
		#写入第一个数据
		write_to_xml(content,url)

def write_to_xml(content,url):

	#打开文档，使用parse方法解析
	parser = etree.XMLParser(remove_blank_text = True)
	xml = etree.parse(url,parser)

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
					"details":item["person_msg"] + item["detail_msg"],
				}
				write_msg(content,saveurl)
			except Exception as ex: 
				print(str(ex))

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

	#需要爬取的数据量
	total = int(input("请输入需要爬取的数据量:"))
	#需要保存的文件名
	savefilename = input("请输入需要保存的文件名:")

	if savefilename.replace(" ","'") != "":
		saveurl = "../Data/" + savefilename + ".xml"
	else:	
			saveurl = "../Data/Opera_character_by_Xikao.xml"
	#爬取www.xikao.com网站的京剧名家
	getXikao(total,saveurl)
	

