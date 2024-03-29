# -*- coding: utf-8 -*-
"""Copy of CNN-Web Deployment.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1e_N88sM8CTu_SPiTmrBCB5pS03vWGHKs
"""

!pip install tensorflow==2.9.1
import tensorflow as tf

print(tf.__version__)

from google.colab import drive
drive.mount('/content/gdrive')

!pip install opendatasets

import opendatasets as od

dataset_url='https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset'

od.download(dataset_url)

import os 

print('Training Folder')
for dirpath,filename,dirname in os.walk('/content/new-plant-diseases-dataset/New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)/train'):
  print(f'There are {len(filename)} directories,{len(dirname)} images in {dirpath}')

print('Testing Folder')
for dirpath,filename,dirname in os.walk('/content/new-plant-diseases-dataset/New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)/valid'):
  print(f'There are {len(filename)} directories,{len(dirname)} images in {dirpath}')

from tensorflow.keras.preprocessing import image_dataset_from_directory

train_dir = '/content/new-plant-diseases-dataset/New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)/train'
test_dir = '/content/new-plant-diseases-dataset/New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)/valid'

train_data = image_dataset_from_directory(train_dir,
                                             image_size=(224,224),
                                             label_mode='categorical',
                                             batch_size=32)

test_data = image_dataset_from_directory(test_dir,
                                         image_size=(224,224),
                                         label_mode='categorical',
                                         batch_size=32)

train_data,test_data

class_names = train_data.class_names
class_names

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import random
import os 
def get_random_image(directory,class_names=class_names):
  rn = random.randint(0,len(class_names)-1)
  choice = random.choice(os.listdir(os.path.join(directory,class_names[rn])))
  img_path= os.path.join(directory,class_names[rn],choice)
  img = mpimg.imread(img_path)
  plt.imshow(img)
  fontsize=10
  plt.title(class_names[rn],fontdict={'fontsize': fontsize})
  plt.axis(False)

plt.figure(figsize=(10,8))
for i in range(9):
  plt.subplot(3,3,i+1)
  get_random_image(train_dir)

import tensorflow as tf
from tensorflow.keras import layers

image_shape = (224,224,3)

base_model = tf.keras.applications.EfficientNetB0(include_top=False,)
base_model.trainable = False

inputs =  layers.Input(shape = image_shape,name='input_layer')

x = base_model(inputs)

x = layers.GlobalAveragePooling2D(name='GlobalAveragePooling2D_layer')(x)

outputs = layers.Dense(38,activation='softmax',name='output_layer')(x)

feature_model = tf.keras.Model(inputs,outputs,name='plant_disease_model')

base_model.trainable = True

for layer in base_model.layers[:-20]:
  layer.trainable = False

feature_model.compile(loss='categorical_crossentropy',
                      optimizer=tf.keras.optimizers.Adam(),
                      metrics=['accuracy'])

import datetime

def create_tensorboard_callback(dir_name, experiment_name):
  log_dir = dir_name + "/" + experiment_name + "/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
  tensorboard_callback = tf.keras.callbacks.TensorBoard(
      log_dir=log_dir
  )
  print(f"Saving TensorBoard log files to: {log_dir}")
  return tensorboard_callback

early_stopping = tf.keras.callbacks.EarlyStopping(monitor="val_loss", 
                                                  patience=3)

reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss",  
                                                 factor=0.2, 
                                                 patience=2,
                                                 verbose=1, 
                                                 min_lr=1e-7)

checkpoint_path = "fine_tune_checkpoints/"
model_checkpoint = tf.keras.callbacks.ModelCheckpoint(checkpoint_path,
                                                      save_weights_only=True,
                                                      save_best_only=True,
                                                      monitor="val_loss")

initial_epochs = 1

history1 = feature_model.fit(
    train_data,
    epochs=initial_epochs,
    validation_data=test_data,
    callbacks=[
        early_stopping,
        model_checkpoint,
        reduce_lr,
        create_tensorboard_callback('plant_disease_model', 'EfficientNetB010')
    ]
)

checkpoint_path = "fine_tune_checkpoints/"

feature_model.load_weights(checkpoint_path)

evaluation_results = feature_model.evaluate(test_data)

from tensorflow.keras.models import load_model

feature_model.save('best_plant_model.h5')

model = load_model('best_plant_model.h5')

tf.keras.models.save_model(feature_model,'my_model2.hdf5')

import pickle

with open('plant.pkl', 'wb') as f:
 pickle.dump(model,f)

def load_prep(img_path):
  img = tf.io.read_file(img_path)

  img = tf.image.decode_image(img)

  img = tf.image.resize(img,size=(224,224))

  return img

image = load_prep('/content/new-plant-diseases-dataset/test/test/AppleCedarRust1.JPG')
plt.imshow(image/255.)
plt.title('AppleCedarRust1.JPG')
plt.suptitle(image.shape)

pred = feature_model.predict(tf.expand_dims(image,axis=0))
pred

class_names = test_data.class_names

def random_image_predict(model,test_dir=test_dir,class_names=class_names,rand_class=True,cls_name=None):
  if rand_class==True:
    ran_cls = random.randint(0,len(class_names))
    cls = class_names[ran_cls]
    ran_path = test_dir +'/'+ cls+ '/'+ random.choice(os.listdir(test_dir+'/'+cls))
  else:
    cls = class_names[cls_name]
    ran_path = test_dir +'/'+ cls + '/'+ random.choice(os.listdir(test_dir+'/'+cls))
  
  prep_img = load_prep(ran_path)

  pred = model.predict(tf.expand_dims(prep_img,axis=0))
  pred_cls = class_names[pred[0].argmax()]
  pred_percent = pred[0][pred[0].argmax()]*100
  plt.imshow(prep_img/255.)
  if pred_cls == cls:
    c = 'g'
  else:
    c = 'r'
  plt.title(f'actual:{cls},\npred:{pred_cls},\nprob:{pred_percent:.2f}%',color = c ,fontdict={'fontsize':10})
  plt.axis(False)

random_image_predict(feature_model)

plt.figure(figsize=(15,15))
for i in range(9):
  plt.subplot(3,3,i+1)
  random_image_predict(feature_model,test_dir)

data_dir='/content/new-plant-diseases-dataset/test/test'
plt.figure(figsize=(15,10))
for i in range(9):
  plt.subplot(3,3,i+1)
  rn = random.choice(os.listdir(data_dir))
  image_path=os.path.join(data_dir,rn)
  img = load_prep(image_path)
  pred = feature_model.predict(tf.expand_dims(img,axis=0))
  pred_name = class_names[pred.argmax()]
  plt.imshow(img/255.)
  plt.title(f'true:{rn} \npred_class:{pred_name}')
  plt.axis(False)

def predict_img(img_path,model=feature_model,):
  img = load_prep(img_path)

  pred = model.predict(tf.expand_dims(img,axis=0))

  pred_name = class_names[pred.argmax()]

  plt.imshow(img/255.)
  plt.title(f'predicted_class : {pred_name}')
  plt.axis(False)

!wget https://www.agric.wa.gov.au/sites/gateway/files/styles/landscape_large/public/Apple%20scab%20-%20mature%20infection%20on%20leaves.jpg?itok=ftqPUwHl

predict_img('Apple scab - mature infection on leaves.jpg')



"""*Deploy*"""

!pip install streamlit

# Commented out IPython magic to ensure Python compatibility.
# %%writefile app.py
# import streamlit as st
# import tensorflow as tf
# import cv2
# from PIL import Image, ImageOps
# import numpy as np
# 
# class_names = ["Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust",
#                "Apple___healthy", "Blueberry___healthy", "Cherry_(including_sour)___Powdery_mildew","Cherry_(including_sour)___healthy",
#                "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot", "Corn_(maize)___Common_rust_",
#                "Corn_(maize)___Northern_Leaf_Blight", "Corn_(maize)___healthy", "Grape___Black_rot",
#                "Grape___Esca_(Black_Measles)", "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape___healthy",
#                "Orange___Haunglongbing_(Citrus_greening)", "Peach___Bacterial_spot", "Peach___healthy",
#                "Pepper_bell___Bacterial_spot","Pepper_bell___healthy","Potato___Early_blight", "Potato___Late_blight",
#                "Potato___healthy", "Raspberry___healthy", "Soybean___healthy", "Squash___Powdery_mildew",
#                "Strawberry___Leaf_scorch", "Strawberry___healthy", "Tomato___Bacterial_spot",
#                "Tomato___Early_blight","Tomato___Late_blight" "Tomato___Leaf_Mold", "Tomato___Septoria_leaf_spot",
#                "Tomato___Spider_mites Two-spotted_spider_mite", "Tomato___Target_Spot",
#                "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___Tomato_mosaic_virus", "Tomato___healthy"]
# 
# class SessionState:
#     def __init__(self):
#         self.cache = {}
# 
# # Create a SessionState object
# session_state = SessionState()
# 
# def load_model():
#     model = tf.keras.models.load_model('/content/best_plant_model.h5')
#     return model
# 
# def get_model():
#     if 'model' not in session_state.cache:
#         session_state.cache['model'] = load_model()
#     return session_state.cache['model']
# 
# model = get_model()
# 
# st.write("""
#          # Leaf disease detection
#          """
#          )
# 
# file = st.file_uploader("Please upload a brain scan file", type=["jpg", "png"])
# 
# st.set_option('deprecation.showfileUploaderEncoding', False)
# 
# def import_and_predict(image_data, model):
#     size = (224, 224)
#     image = ImageOps.fit(image_data, size, Image.ANTIALIAS)
#     image = np.asarray(image)
#     img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#     img_reshape = img[np.newaxis, ...]
#     pred = model.predict(img_reshape)
#     return pred
# 
# if file is None:
#     st.text("Please upload an image file")
# else:
#     image = Image.open(file)
#     st.image(image, use_column_width=True)
#     predictions = import_and_predict(image, model)
#     score = tf.nn.softmax(predictions[0])
#     st.write(predictions)
#     st.write(score)
#     predicted_class_index = np.argmax(score)
#     predicted_class_name = class_names[predicted_class_index]
#     st.write("Predicted Class:", predicted_class_name)
#

!nohup streamlit run app.py &

!pip install pyngrok

!wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip

!unzip ngrok-stable-linux-amd64.zip

!ngrok config add-authtoken 2PManWbX9xCVK0axH4R5uKDohgl_5mecrjc6G1R3y6vFcjzqC

get_ipython().system_raw('./ngrok http 8501 &')

!curl -s http://localhost:4040/api/tunnels | python3 -c \
    'import sys, json; print("Execute the next cell and the go to the following URL: " +json.load(sys.stdin)["tunnels"][0]["public_url"])'

!streamlit run /content/app.py