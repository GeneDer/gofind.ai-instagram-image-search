#!/usr/locals/python
#author:Shanglin Yang(kudoysl@gmail.com)

import os
import sys
import cv2
import glob
import tensorflow as tf
import numpy as np
import time
import sqlite3
import base64
from requests import Request, Session
import json

from tensorflow.python.platform import gfile
from tensorflow.python.framework import graph_util
from six.moves import cPickle as pickle

threshold = 0.2
iou_threshold = 0.5
img_name = ''
image_width = 0
image_height = 0
classes = ["bags","top", "bottom", "TopInnerwear", "BottomInnerwear", "dress", "Outerwear", "footwear", "headwear", "neckwear", "belt", "eyewear"]


conn = sqlite3.connect('instagram.db')
cur = conn.cursor()
cur.execute("""SELECT MAX(id) FROM posts""")
rows = cur.fetchall()
if rows[0][0]:
    image_id = rows[0][0] + 1
else:
    image_id = 1

cur.execute("""SELECT MAX(id) FROM segmented""")
rows = cur.fetchall()
if rows[0][0]:
    segm_id = rows[0][0] + 1
else:
    segm_id = 1


def show_results(img,results):
    import base64
    global img_name,segm_id

    count = 0
    for i in range(len(results)):
        x = int(results[i][1])
        y = int(results[i][2])
        w = int(results[i][3])//2
        h = int(results[i][4])//2

        if (results[i][0] == 'footwear' and results[i][5] > 0.4) or \
           (results[i][0] != 'footwear' and results[i][5] > 0.3):
            img_cp = img.copy()
            img_cp = img_cp[y-h:y+h, x-w:x+w]
            img_path = "./output/"+img_name+"_"+str(count)+"_seg.jpg"
            cv2.imwrite(img_path,img_cp)

            cur.execute("""INSERT INTO segmented
                           (id, segmented_image_path, classes,
                           cx, cy, w, h, confidence, post_id)
                           VALUES (%s,'%s','%s',%s,%s,%s,%s,
                           %s,%s)"""%(segm_id, img_path, results[i][0],
                                      results[i][1], results[i][2],
                                      results[i][3], results[i][4],
                                      results[i][5], image_id))
            conn.commit()

            with open(img_path, "rb") as image_file:
                api_input = {"img64":base64.b64encode(image_file.read())}
                
            s = Session()
            req = Request('POST', "http://www.gofindapi.com:3000/searchapi",
                          data=json.dumps(api_input), headers={'Content-Type':"application/json"})
            prepped = req.prepare()
            resp = s.send(prepped)
            
            api_output = json.loads(resp.content)
            if 'data' in api_output:
                print len(api_output['data'])
                #insert into database
                for result in api_output['data']:
                    image_url = result['reference_image_links'][0]
                    seller_url = result['url']
                    seller_name = result['seller']
                    item_name = result['itemName']
                    if type(result['price']) == list:
                        price = result['price'][0]
                    else:
                        price = result['price']
                        
                    cur.execute("""INSERT INTO results
                                   (segmented_id, image_url, seller_url,
                                   seller_name, item_name, price)
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                [segm_id, image_url, seller_url,
                                 seller_name, item_name, price])
                    conn.commit()
                    
            segm_id += 1
            count += 1
            

def iou(box1,box2):
    tb = min(box1[0]+0.5*box1[2],box2[0]+0.5*box2[2])-max(box1[0]-0.5*box1[2],box2[0]-0.5*box2[2])
    lr = min(box1[1]+0.5*box1[3],box2[1]+0.5*box2[3])-max(box1[1]-0.5*box1[3],box2[1]-0.5*box2[3])
    if tb < 0 or lr < 0 : intersection = 0
    else : intersection =  tb*lr
    return intersection / (box1[2]*box1[3] + box2[2]*box2[3] - intersection)

def interpret_output(output):
    
    global img_name
    global image_width,image_height
    
    probs = np.zeros((7,7,2,12))
    class_probs = np.reshape(output[0:588],(7,7,12))
    scales = np.reshape(output[588:686],(7,7,2))
    boxes = np.reshape(output[686:],(7,7,2,4))
    offset = np.transpose(np.reshape(np.array([np.arange(7)]*14),(2,7,7)),(1,2,0))

    boxes[:,:,:,0] += offset
    boxes[:,:,:,1] += np.transpose(offset,(1,0,2))
    boxes[:,:,:,0:2] = boxes[:,:,:,0:2] / 7.0
    boxes[:,:,:,2] = np.multiply(boxes[:,:,:,2],boxes[:,:,:,2])
    boxes[:,:,:,3] = np.multiply(boxes[:,:,:,3],boxes[:,:,:,3])
        
    boxes[:,:,:,0] *= image_width
    boxes[:,:,:,1] *= image_height
    boxes[:,:,:,2] *= image_width
    boxes[:,:,:,3] *= image_height

    for i in range(2):
        for j in range(12):
            probs[:,:,i,j] = np.multiply(class_probs[:,:,j],scales[:,:,i])

    filter_mat_probs = np.array(probs>=threshold,dtype='bool')
    filter_mat_boxes = np.nonzero(filter_mat_probs)
    boxes_filtered = boxes[filter_mat_boxes[0],filter_mat_boxes[1],filter_mat_boxes[2]]
    probs_filtered = probs[filter_mat_probs]
    classes_num_filtered = np.argmax(filter_mat_probs,axis=3)[filter_mat_boxes[0],filter_mat_boxes[1],filter_mat_boxes[2]] 

    argsort = np.array(np.argsort(probs_filtered))[::-1]
    boxes_filtered = boxes_filtered[argsort]
    probs_filtered = probs_filtered[argsort]
    classes_num_filtered = classes_num_filtered[argsort]
        
    for i in range(len(boxes_filtered)):
        if probs_filtered[i] == 0 :
            continue
        for j in range(i+1,len(boxes_filtered)):
            if iou(boxes_filtered[i],boxes_filtered[j]) > iou_threshold : 
                probs_filtered[j] = 0.0

        filter_iou = np.array(probs_filtered>0.0,dtype='bool')
        boxes_filtered = boxes_filtered[filter_iou]
        probs_filtered = probs_filtered[filter_iou]
        classes_num_filtered = classes_num_filtered[filter_iou]

        result = []
        for i in range(len(boxes_filtered)):
            result.append([classes[classes_num_filtered[i]],boxes_filtered[i][0],boxes_filtered[i][1],boxes_filtered[i][2],boxes_filtered[i][3],probs_filtered[i]])

        return result

def process_image(img,sess):
    
    input_tensor = "input:0"
    output_name = "output:0"
    
    img_resized = cv2.resize(img, (448,448 ))
    img_resized_np = np.asarray( img_resized )
    inputs = np.zeros((1,448,448,3),dtype= "float32")
    inputs[0] = (img_resized_np/255.0)*2.0-1.0

    out_tensor = sess.graph.get_tensor_by_name(output_name)
    output = sess.run([out_tensor], {input_tensor: inputs})
    
    results = interpret_output(output[0][0])
    #print results

    if (results):
        show_results(img,results)

def main(img_list, username):
    cur.execute("""INSERT INTO users
                   (username)
                   VALUES ('%s')"""%(username))
    conn.commit()

    global img_name
    global image_width,image_height,image_id
        
    graph_path = "./YOLO_new_constant.pb"
    #img_list = "./image_list.txt"

    ######################################################################
    # Unpersists graph from file
    with tf.gfile.FastGFile(graph_path, 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        _ = tf.import_graph_def(graph_def, name='')
    ######################################################################

    config = tf.ConfigProto(
        device_count = {'GPU': 0}
    )
    with tf.Session(config=config) as sess:
        with open(img_list) as f:
            for img_path in f:
                
                cur.execute("""INSERT INTO posts
                             (id, main_image_path, username)
                             VALUES (%s,'%s','%s')
                             """%(image_id,
                                  img_path.strip(),
                                  username))
                conn.commit()
                
                if True:
                    img_name = img_path[img_path.rfind('/')+1:-5]
                    image = cv2.imread(img_path[:-1])
                    image_height,image_width,_ = image.shape
                    process_image(image,sess)
                else:
                    pass

                image_id += 1
    
    #conn.close()
    return "Success"

if __name__ == "__main__":
    main(img_list="input/3957083551.8185d1b.66764f053cce446a95ce0a48eeaa194c.txt",
         username="gofind.fashion")
