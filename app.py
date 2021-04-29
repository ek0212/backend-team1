from flask import Flask , render_template, request, send_file
import os
import matplotlib.pyplot as plt
from style_transfer import *
from flask import send_file
from flask_cors import CORS

app = Flask(__name__)
UPLOAD_FOLDER = './static/image/upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
style =""
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

cors = CORS(app)

@app.route("/")
def home():
	return render_template("index.html")


@app.route("/stylize", methods=['GET','POST'])
def upload_file():
	print("Hi from stylize") #sanity check
	content = request.files['image']
	style = request.form.get('style')

	if (style == ''):
		print("No style choice was given")
	
	content.save(os.path.join(app.config['UPLOAD_FOLDER'], content.filename))
	#load in content and style image
	content = load_image('./static/image/upload/'+content.filename)
	#resize style to match content, makes code easier
	style = load_image('./static/image/'+ style+'.jpg', shape=content.shape[-2:])

	vgg = model()
	target = stylize(content,style,vgg)
	x = im_convert(target)
	
	# image = Image.fromarray(x)
	x.save("result.jpg")
	return send_file("result.jpg", mimetype='image/jpg')

@app.route('/result')
def get_res():
	print("Hi from result") #sanity check
	return send_file("result.jpg", mimetype='image/jpg')
							

if __name__ =="__main__":
	app.run(host='0.0.0.0', port=5000, debug=True)
