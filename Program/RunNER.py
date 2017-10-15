#coding:utf-8
from stanza.nlp.corenlp import CoreNLPClient
from lxml import etree
import re
import ProcessMes as pm
import os


def doNER(url):
	
	#Stanford NER本地服务器启动，在Core NLP的工作目录下输入
	#java -Xmx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -serverProperties StanfordCoreNLP-chinese.properties -port 9000 -timeout 15000
	client = CoreNLPClient(server='http://localhost:9000', default_annotators=['ssplit', 'lemma', 'tokenize', 'pos', 'ner']) 

	num = 0
	for name,details in pm.getDetailMes("../Data/Opera_characters_Xikao_1000.xml"):
		num+=1 
		print("处理第" + str(num) + "条数据")
		
		name_list = [name]
		location_list = []
		operaname_list = []


		#命名实体识别，通过《》识别戏曲名
		re_str = "(《.*?》)"
		pattern = re.compile(re_str,re.S)

		items = re.findall(pattern,details)
		for item in items:
			if item not in operaname_list:
				operaname_list.append(item)

		#将戏曲名替换，防止戏曲名中的姓名和地名被识别
		details = re.sub(pattern,"#",details)	

		#命名实体识别,识别姓名和地名
		annotated = client.annotate(details)	
		for sentence in annotated.sentences:
			for token in sentence:
				if token.ner == "PERSON":
					if token.word not in name_list and len(token.word) != 1:
							name_list.append(token.word)
				if token.ner == "GPE":
					if token.word not in location_list and len(token.word) != 1:
						location_list.append(token.word)

		#将3个命名实体写入新的xml
		content = {
			"Index":num,
			"name":name,
			"name_list":name_list,
			"location_list":location_list,
			"operaname_list":operaname_list
		}
		create_entity_xml(content,url)

#将命名实体写入xml
def create_entity_xml(content,url):

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
	childnode = {}
	#创造子节点
	Performers_node = etree.SubElement(root,"Performers")
	Performers_node.set("name",content["name"])

	orders = ["Index","name","name_list","location_list","operaname_list"]
	#为子节点加入文本
	for key in orders:
		print(key)
		value = content[key]
		#判断value是否为数组
		if type(value) == list:
			childnode[key] = etree.SubElement(Performers_node,key)
			for i in range(len(value)):
				node[key] = etree.SubElement(childnode[key],key+"_value")
				node[key].text = str(value[i])
		else:
			node[key] = etree.SubElement(Performers_node,key)
			node[key].text = str(value)

	#保存文档
	tree = etree.ElementTree(root)  
	tree.write(url, pretty_print=True, xml_declaration=True, encoding='utf-8')

if __name__ == "__main__":
	doNER("../Data/Named_Entities.xml")
