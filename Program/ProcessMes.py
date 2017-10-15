#coding:utf-8
from lxml import etree

#从爬取的Opera_Characters_Xikao_1000.xml中获得人物详细介绍正文
def getDetailMes(filename):
	#打开文档
	parser = etree.XMLParser(remove_blank_text=True)
	xml = etree.parse(filename,parser)

	root = xml.getroot()
	num = 1
	for node in root.xpath("//Performers"):
		num+=1
		for childnode in node.getchildren():
			if childnode.tag == "name":
				name = childnode.text
			if childnode.tag == "details":
				details = childnode.text
		yield name,details


#从xml从提取出人物介绍信息转化为txt文本
def detail_to_txt(path):
	for name,details in getDetailMes("../Data/Opera_characters_Xikao_1000.xml"):
		text = name + "，" + details
		filename = path + "/" + name + ".txt"
		with open(filename,"w",encoding="utf-8") as f:
			f.write(text)


if __name__ == "__main__":
	detail_to_txt("../Data/txt_details")