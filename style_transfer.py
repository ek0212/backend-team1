# -*- coding: utf-8 -*-

from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.optim as optim
from torchvision import transforms, models


def model():
  # get the "features" portion of VGG19 (we will not need the "classifier" portion)
  vgg = models.vgg19(pretrained=True).features
  
  # freeze all VGG parameters since we're only optimizing the target image
  for param in vgg.parameters():
      param.requires_grad_(False)
 
  return vgg

def load_image(img_path, max_size=400, shape=None):
    ''' Load in and transform an image, making sure the image
       is <= 400 pixels in the x-y dims.'''
    
    image = Image.open(img_path).convert('RGB')
    
    # large images will slow down processing
    if max(image.size) > max_size:
        size = max_size
    else:
        size = max(image.size)

    if shape is not None:
        size = shape
        
    in_transform = transforms.Compose([
                        transforms.Resize(size),
                        transforms.ToTensor(),
                        transforms.Normalize((0.485, 0.456, 0.406), 
                                             (0.229, 0.224, 0.225))])

    # discard the transparent, alpha channel (that's the :3) and add the batch dimension
    image = in_transform(image)[:3,:,:].unsqueeze(0)
    
    return image



# helper function for un-normalizing an image 
# and converting it from a Tensor image to a NumPy image for display
def im_convert(tensor):
    """ Display a tensor as an image. """
    
    image = tensor.to("cpu").clone().detach()
    image = image.numpy().squeeze()
    image = image.transpose(1,2,0)
    image = image * np.array((0.229, 0.224, 0.225)) + np.array((0.485, 0.456, 0.406))
    image = image.clip(0, 1)

    return image



def get_features(image, model, layers=None):
    """ Run an image forward through a model and get the features for 
        a set of layers. Default layers are for VGGNet matching Gatys et al (2016)
    """
    
   
    if layers is None:
        layers = {'0': 'conv1_1',
                  '5': 'conv2_1', 
                  '10': 'conv3_1', 
                  '19': 'conv4_1',
                  '21': 'conv4_2',  ## content representation
                  '28': 'conv5_1'}
        
        
   
    features = {}
    x = image
    
    # model._modules is a dictionary holding each module in the model
    for name, layer in model._modules.items():
        x = layer(x)
        if name in layers:
            features[layers[name]] = x
            
    return features

def gram_matrix(tensor):
    
    _,depth,height, width = tensor.size()
    
    # reshape so we're multiplying the features for each channel
    tensor = tensor.view(depth, height * width)
    
    # calculate the gram matrix
    gram = torch.mm(tensor, tensor.t())
    
    return gram

# set num_iterations to 150
def stylize(content,style,model,num_iterations=150):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # load in content and style image
    content = content.to(device)
    # resize style to match content, makes code easier
    style = style.to(device)
    vgg = model.to(device)
    # get content and style features only once before forming the target image
    content_features = get_features(content, vgg)
    style_features = get_features(style, vgg)

    # calculate the gram matrices for each layer of our style representation
    style_grams = {layer: gram_matrix(style_features[layer]) for layer in style_features}

    # create a third "target" image and prep it for change
    # it is a good idea to start of with the target as a copy of our *content* image
    # then iteratively change its style
    target = content.clone().requires_grad_(True).to(device)
    
    style_weights = {'conv1_1': 0.6,
                 'conv2_1': 0.5,
                 'conv3_1': 0.5,
                 'conv4_1': 0.8,
                 'conv5_1': 0.8}

    content_weight = 1  # alpha
    style_weight = 1e5  # beta
    # iteration hyperparameters
    optimizer = optim.Adam([target], lr=0.003)

    for ii in range(1, num_iterations+1):

        ## get the features from your target image    
        ## then calculate the content loss
        target_features = get_features(target, vgg)

        content_loss =torch.mean((target_features['conv4_2'] - content_features['conv4_2'])**2)

        # the style loss
        # initialize the style loss to 0
        style_loss = 0
        # iterate through each style layer and add to the style loss
        for layer in style_weights:
            # get the "target" style representation for the layer
            target_feature = target_features[layer]
            target_gram = gram_matrix(target_feature)
            _, d, h, w = target_feature.shape

            #get the "style" style representation
            style_gram = style_grams[layer]

          ## calculate the style loss for one layer, weighted appropriately
            layer_style_loss = style_weights[layer] * torch.mean((target_gram - style_gram)**2)
            # add to the style loss
            style_loss += layer_style_loss / (d * h * w)

        ## calculate the *total* loss
        total_loss = content_weight * content_loss + style_weight * style_loss

        # update your target image
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()
    return target







