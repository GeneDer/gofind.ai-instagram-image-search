from flask import Flask
from requests import Request, Session
import json
import urllib
import time

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/gofind-instagram-api/<access_token>')
def instagram_api(access_token):
    s = Session()
    req = Request('GET', "https://api.instagram.com/v1/users/self/?access_token=%s"%access_token)
    prepped = req.prepare()
    resp = s.send(prepped)
    username = json.loads(resp.content)['data']['username']
    
    s = Session()
    req = Request('GET', "https://api.instagram.com/v1/users/self/media/recent/?COUNT=250&amp;access_token=%s"%access_token)
    prepped = req.prepare()
    resp = s.send(prepped)

    data = json.loads(resp.content)
    img_list = "input/"+access_token+".txt"
    with open(img_list, 'w') as f:
        for i in xrange(len(data['data'])):
            url = data['data'][i]['images']['standard_resolution']['url']
            file_path = "input/"+access_token+"_"+str(i)+'.jpg'
            urllib.urlretrieve(url,file_path)
            f.write(file_path+'\n')

        
    import yolo        
    return_value = yolo.main(img_list, username)
    if return_value:
        return return_value
    else:
        return "Fail"

if __name__ == '__main__':
    app.run()

