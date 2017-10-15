import tensorflow as tf
import numpy as np
import time
import datetime
import os
import re
import network
from stanza.nlp.corenlp import CoreNLPClient
from sklearn.metrics import average_precision_score
from numpy._distributor_init import NUMPY_MKL


#Stanford NER本地服务器启动，在Core NLP的工作目录下输入
#java -Xmx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -serverProperties StanfordCoreNLP-chinese.properties -port 9000 -timeout 15000
client = CoreNLPClient(server='http://localhost:9000', default_annotators=['ssplit', 'lemma', 'tokenize', 'pos', 'ner']) 

def pos_embed(x):
    if x < -60:
        return 0
    if -60 <= x <= 60:
        return x + 61
    if x > 60:
        return 122

#导入进行关系抽取的模型
def openmodel():
    pathname = "./model/ATT_GRU_model-9000"
    wordembedding = np.load('./data/vec.npy')
    test_settings = network.Settings()
    test_settings.vocab_size = 16693
    test_settings.num_classes = 12
    test_settings.big_num = 1
    
    with tf.Graph().as_default():
        sess = tf.Session()
        with sess.as_default():
            def test_step(word_batch, pos1_batch, pos2_batch, y_batch):

                feed_dict = {}
                total_shape = []
                total_num = 0
                total_word = []
                total_pos1 = []
                total_pos2 = []

                for i in range(len(word_batch)):
                    total_shape.append(total_num)
                    total_num += len(word_batch[i])
                    for word in word_batch[i]:
                        total_word.append(word)
                    for pos1 in pos1_batch[i]:
                        total_pos1.append(pos1)
                    for pos2 in pos2_batch[i]:
                        total_pos2.append(pos2)

                total_shape.append(total_num)
                total_shape = np.array(total_shape)
                total_word = np.array(total_word)
                total_pos1 = np.array(total_pos1)
                total_pos2 = np.array(total_pos2)

                feed_dict[mtest.total_shape] = total_shape
                feed_dict[mtest.input_word] = total_word
                feed_dict[mtest.input_pos1] = total_pos1
                feed_dict[mtest.input_pos2] = total_pos2
                feed_dict[mtest.input_y] = y_batch

                loss, accuracy, prob = sess.run(
                    [mtest.loss, mtest.accuracy, mtest.prob], feed_dict)
                return prob, accuracy
            
            
            with tf.variable_scope("model"):
                mtest = network.GRU(is_training=False, word_embeddings=wordembedding, settings=test_settings)

            names_to_vars = {v.op.name: v for v in tf.global_variables()}
            saver = tf.train.Saver(names_to_vars)
            saver.restore(sess, pathname)
            
            print('reading word embedding data...')
            vec = []
            word2id = {}
            f = open('./origin_data/vec.txt', encoding='utf-8')
            content = f.readline()
            content = content.strip().split()
            dim = int(content[1])
            while True:
                content = f.readline()
                if content == '':
                    break
                content = content.strip().split()
                word2id[content[0]] = len(word2id)
                content = content[1:]
                content = [(float)(i) for i in content]
                vec.append(content)
            f.close()
            word2id['UNK'] = len(word2id)
            word2id['BLANK'] = len(word2id)
            
            print('reading relation to id')
            relation2id = {}
            id2relation = {}
            f = open('./origin_data/relation2id.txt', 'r', encoding='utf-8')
            while True:
                content = f.readline()
                if content == '':
                    break
                content = content.strip().split()
                relation2id[content[0]] = int(content[1])
                id2relation[int(content[1])] = content[0]
            f.close()
    return word2id,relation2id,id2relation,test_step

#输入两个姓名和句子进行关系预测，其他参数是进行预测需要的模型参数            
def predict(en1,en2,sentence,word2id,relation2id,id2relation,test_step):
    #start predict
    #line = input('请输入中文句子，格式为 "name1 name2 sentence":')
    #en1, en2, sentence = line.strip().split()
    #print("实体1: " + en1)
    #print("实体2: " + en2)
    #print(sentence)
    test_settings = network.Settings()
    test_settings.vocab_size = 16693
    test_settings.num_classes = 12
    test_settings.big_num = 1

    relation = 0
    en1pos = sentence.find(en1)
    if en1pos == -1:
        en1pos = 0
    en2pos = sentence.find(en2)
    if en2pos == -1:
        en2post = 0
    output = []
    # length of sentence is 70
    fixlen = 70
    # max length of position embedding is 60 (-60~+60)
    maxlen = 60

    #Encoding test x
    for i in range(fixlen):
        word = word2id['BLANK']
        rel_e1 = pos_embed(i - en1pos)
        rel_e2 = pos_embed(i - en2pos)
        output.append([word, rel_e1, rel_e2])

    for i in range(min(fixlen, len(sentence))):
        
        word = 0
        if sentence[i] not in word2id:
            #print(sentence[i])
            #print('==')
            word = word2id['UNK']
            #print(word)
        else:
            #print(sentence[i])
            #print('||')
            word = word2id[sentence[i]]
            #print(word)
            
        output[i][0] = word
    test_x = []
    test_x.append([output])
    
    #Encoding test y
    label = [0 for i in range(len(relation2id))]
    label[0] = 1
    test_y = []
    test_y.append(label)
    
    test_x = np.array(test_x)
    test_y = np.array(test_y)
    
    test_word = []
    test_pos1 = []
    test_pos2 = []

    for i in range(len(test_x)):
        word = []
        pos1 = []
        pos2 = []
        for j in test_x[i]:
            temp_word = []
            temp_pos1 = []
            temp_pos2 = []
            for k in j:
                temp_word.append(k[0])
                temp_pos1.append(k[1])
                temp_pos2.append(k[2])
            word.append(temp_word)
            pos1.append(temp_pos1)
            pos2.append(temp_pos2)
        test_word.append(word)
        test_pos1.append(pos1)
        test_pos2.append(pos2)

    test_word = np.array(test_word)
    test_pos1 = np.array(test_pos1)
    test_pos2 = np.array(test_pos2)
    
    prob, accuracy = test_step(test_word, test_pos1, test_pos2, test_y)
    prob = np.reshape(np.array(prob), (1, test_settings.num_classes))[0]
    #print("关系是:")
    top3_id = prob.argsort()[-3:][::-1]
    flags = False
    ans = ""
    for n, rel_id in enumerate(top3_id):
        if id2relation[rel_id] != "unknown" and prob[rel_id] > 0.8:
            if flags == False:
                ans = en1 + " " + en2 + " "
                flags = True
            ans += (id2relation[rel_id] + " 概率为:" + str(prob[rel_id]))
    return ans

#获取path所有txt文本中的
def getRelationship(path,savepath):

    files = os.listdir(path)
    count = 0

    #打开实体关系识别的模型
    word2id,relation2id,id2relation,test_step = openmodel()
    
    for filename in files:
        count+=1
        filepath = path + "/" + filename
        print("处理第" + str(count) + "条数据")

        with open(filepath,"r",encoding="utf-8") as file:
            text = file.read()

        #处理戏曲名，使用#替换
        pattern = re.compile("(《.*?》)")
        text = re.sub(pattern,"",text)

        name = ""
        #获取本人姓名
        annotated = client.annotate(text[0])
        for sen in annotated.sentences:
            #print(sen)
            for token in sen:
                #print(token.word,token.ner)
                if token.ner == "PERSON" and len(token.word) != 1:
                        name = token.word
                        ans = name + "---------->"
        if name == "":
            name = filename.split(".")[0]

        #识别出该文本中的所有人名
        relationships= []
        annotated = client.annotate(text)
        relationship = []
        for sentence in annotated.sentences:
            for token in sentence:
                if token.ner == "PERSON":
                    if token.word != name and len(token.word) != 1:
                        str_relation = predict(name,token.word,str(sentence),word2id,relation2id,id2relation,test_step)
                        if str_relation != "":
                            relationship.append(str_relation)
        if len(relationship) != 0 :
            relationships.append(relationship)
            #print(relationship)


        with open(savepath,"a",encoding="utf-8") as f:
            f.write("\n" + name +"----------->\n")
            for lists in relationships:
                for strs in lists:
                    f.write(strs+"\n")


if __name__ == "__main__":

    path = input("请输入需要处理的路径(输入为空则默认../../Data/txt_details):")
    savepath = input("请输入需要保存的文件名(输入为空则默认../../Data/OtherMethodRelationship.txt):")

    if path == "":
        path = "../../Data/txt_details"
    if savepath == "":
        savepath = "../../Data/OtherMethodRelationship.txt"
    getRelationship(path,savepath)