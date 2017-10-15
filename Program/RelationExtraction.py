#coding:utf-8
from stanza.nlp.corenlp import CoreNLPClient
from lxml import etree
import re
import ProcessMes as pm
import os
from lxml import etree

def extraction(path="../Data/txt_details",savepath="../Data/relationship.txt"):

	#Stanford NER本地服务器启动，在Core NLP的工作目录下输入
	#java -Xmx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -serverProperties StanfordCoreNLP-chinese.properties -port 9000 -timeout 15000
	client = CoreNLPClient(server='http://localhost:9000', default_annotators=['ssplit', 'lemma', 'tokenize', 'pos', 'ner']) 

	files = os.listdir(path)
	count = 0

	#师父的正则匹配
	pattern_master = re.compile(r"(.*师从)|(.*(从|向).*学.*)|(.*拜.*)|(.*被.*收为.*)|(.*从师.*)|(.*开蒙(?!戏).*)|" +
			"(.*师承.*)|(.*为师.*)|(.*受.*指导.*)|(.*被.*收为.*)|(.*为.*弟子)|(.*得.*真传.*)|(.*传授.*)|(.*亲授.*)|(入.*习)" )
	
	#弟子的正则匹配
	pattern_student = re.compile(r"(.*培养.*)|(.*收.*弟子.*)")

	#地点的正则匹配
	pattern_location = re.compile(r"(.*(?<!族)人)|(生于.*)")

	#人物和科班/学校的正则匹配
	pattern_school = re.compile(r"(?<!调)(入|从|在|到|考入|毕业于|坐科)(.*?(?<!的))(学校|科班|学院)(?!任教)")
	
	for name in files:
		count+=1
		filename = path + "/" + name
		print("处理第" + str(count) + "个数据")
		with open(filename,"r",encoding="utf-8") as f:
			text = f.read()

		#处理戏曲名，使用#替换
		pattern = re.compile("(《.*?》)")
		text = re.sub(pattern,"",text)
		text = re.split("[。]|[！？]+|[，]|[；]",text)

		#name = name.split(".")[0]
		relationship = [[],[],[],[]]
		location = False
		
		#获取本人姓名
		name = name.split(".")[0]
		annotated = client.annotate(text[0])
		for sen in annotated.sentences:
			#print(sen)
			for token in sen:
				if token.ner == "PERSON" and len(token.word) != 1:
						name = token.word
			

		for sentence in text:
			#师父关系抽取
			match = pattern_master.match(sentence)
			if match:
				annotated = client.annotate(sentence)
				for sen in annotated.sentences:
					#print(sen)
					for token in sen:
						#print(token.word,token.ner)
						if token.ner == "PERSON" and len(token.word) != 1:
							if token.word != name:
								relationship[0].append(token.word + " 师徒 " + name )
			#徒弟关系抽取
			match = pattern_student.match(sentence)
			if match:
				annotated = client.annotate(sentence)
				for sen in annotated.sentences:
					for token in sen:
						if token.ner == "PERSON" and len(token.word) != 1 and token.word != name:
							relationship[1].append(name + " 师徒 " + token.word )

			#地点关系抽取
			match = pattern_location.match(sentence)
			if match and location == False:
				annotated = client.annotate(sentence)
				for sen in annotated.sentences:
					flag = 1
					for token in sen:
						if token.ner == "GPE" or token.ner == "DEMONYM":
							if flag == 1:
								relationship[2].append(name + " 出生地 " + token.word.replace("人","") )
								flag+=1
							else:
								relationship[2][-1] += token.word
							location = True

			#人物和科班/学校关系抽取
			school = pattern_school.findall(sentence)
			if len(school) != 0:
				for item in school:
					school = item[1] 
					if item[2] != "习艺" and item[2] != "坐科":
						school += item[2]
					relationship[3].append(name + " 习艺 " + school)

		#write_to_xml("../Data/Relationship.xml",relationship,name)

		with open(savepath,"a",encoding="utf-8") as f:
			f.write("\n" + name +"----------->\n")
			for lists in relationship:
				for strs in lists:
					f.write(strs+"\n")

#将实体关系写入xml文档中
def write_to_xml(path,relationship,name):

	if os.path.isfile(path):
		#打开文档，使用parse方法解析
		parser = etree.XMLParser(remove_blank_text = True)
		xml = etree.parse(path,parser)
		#获取根节点
		root = xml.getroot()
	else:
		#创建第一个节点,第一个节点就是根节点
		root = etree.Element("root",nsmap={'xsi': 'http://b.c/d'})
		tree = etree.ElementTree(root)

	#创造子节点
	Performers_node = etree.SubElement(root,"Performers")
	Performers_node.set("name",name)

	master_node = etree.SubElement(Performers_node,"Master")
	for strs in relationship[0]:
		master_relationship = etree.SubElement(master_node,"Master_relationship")
		master_relationship.text = strs

	for strs in relationship[1]:
		master_relationship = etree.SubElement(master_node,"Master_relationship")
		master_relationship.text = strs

	Location_node = etree.SubElement(Performers_node,"Location")
	for strs in relationship[2]:
		location_relationship = etree.SubElement(Location_node,"Location_relationship")
		location_relationship.text = strs

	School_node = etree.SubElement(Performers_node,"School")
	for strs in relationship[3]:
		school_relationship = etree.SubElement(School_node,"School_relationship")
		school_relationship.text = strs

	#保存文档
	tree = etree.ElementTree(root)  
	tree.write(path, pretty_print=True, xml_declaration=True, encoding='utf-8')

if __name__ == "__main__":

	path = input("请输入需要处理的路径(输入为空则默认../Data/txt_details):")
	savepath = input("请输入需要保存的文件名(输入为空则默认../Data/Relationship.txt):")

	if path == "":
		path = "../Data/txt_details"
	if savepath == "":
		savepath = "../Data/Relationship.txt"
	extraction(path,savepath)