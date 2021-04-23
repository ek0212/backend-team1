from flask import Flask , render_template, request, send_from_directory
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

# from flask_ngrok import run_with_ngrok
# from flask import Flask
# app = Flask(__name__)
cors = CORS(app)
# run_with_ngrok(app)

# @app.route("/")
# def home():
#     return "<h1>Running Flask on Google Colab!</h1>"

# @app.route('/stylize', methods=['POST'])
# def stylize():
#     input_image = request.files['image']
#     outputter(input_image, '/tmp/nst/1024px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg', num_iterations=300)
#     return send_file("result.jpg", mimetype='image/jpg')

# @app.route('/result')
# def get_res():
#    return send_file("result.jpg", mimetype='image/jpg')

# app.run()

@app.route("/")
def home():
	return render_template("index.html")


@app.route("/stylize", methods=['GET','POST'])
def upload_file():
	print("Hi from stylize")
	content = request.files['image']
	style = request.form.get('style')

	if (style == ''):
		print("No style choice was given")
	
	content.save(os.path.join(app.config['UPLOAD_FOLDER'], content.filename))
	#check image size
	if check_image('./static/image/upload/'+content.filename):
		#load in content and style image
		content = load_image('./static/image/upload/'+content.filename)
		#Resize style to match content, makes code easier
		style = load_image('./static/image/'+ style+'.jpg', shape=content.shape[-2:])

		vgg = model()
		target = stylize(content,style,vgg)
		x = im_convert(target)

		# app.config['UPLOAD_FOLDER'] would need to be a path to Upload_folder for send_from_directory to work
		plt.imsave(app.config['UPLOAD_FOLDER']+'/result.png',x)
		return send_from_directory(app.config['UPLOAD_FOLDER'], "result.png", mimetype='image/png')
	else: 
		print("Image too large, try again.")
		
@app.route('/result')
def get_res():
	print("Hi from result")
	return send_from_directory(app.config["UPLOAD_FOLDER"], "result.png", mimetype='image/png')
							

if __name__ =="__main__":
	app.run(host='0.0.0.0', port=5000, debug=True)
