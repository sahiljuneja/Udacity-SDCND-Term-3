
# coding: utf-8

# In[1]:

import os.path
import tensorflow as tf
import helper
import project_tests as tests


# In[2]:

def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'
    
    
    buff = tf.saved_model.loader.load(sess,
                                      [vgg_tag],
                                      vgg_path)
    
    image_input = tf.get_default_graph().get_tensor_by_name(vgg_input_tensor_name)
    keep_prob = tf.get_default_graph().get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3_out = tf.get_default_graph().get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4_out = tf.get_default_graph().get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7_out = tf.get_default_graph().get_tensor_by_name(vgg_layer7_out_tensor_name)

    
    return image_input, keep_prob, layer3_out, layer4_out, layer7_out
tests.test_load_vgg(load_vgg, tf)


# In[3]:

'''
### Test for layers
data_dir = './data'
tests.test_for_kitti_dataset(data_dir)

# Download pretrained vgg model
helper.maybe_download_pretrained_vgg(data_dir)

vgg_path = './data/vgg'
with tf.Session() as sess:
    input_image, keep_prob, vgg_layer3_out, vgg_layer4_out, vgg_layer7_out = load_vgg(sess, vgg_path)
'''


# In[4]:

def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    
    # TODO_mine: Better layer names
    # xavier_initializer doesn't produce good results at all.
    
    # 1x1 with 7
    layer7 = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, padding='SAME', 
                              kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))

    # 1x1 with 4
    layer4 = tf.layers.conv2d(vgg_layer4_out, num_classes, 1, padding='SAME',
                             kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    
    # 1x1 with 3
    layer3 = tf.layers.conv2d(vgg_layer3_out, num_classes, 1, padding='SAME',
                             kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    
    # Upsample 7 
    upsample7 = tf.layers.conv2d_transpose(layer7, num_classes, 4, 2, 'SAME',
                                          kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    
    # TODO_mine: Look into weighted skip-connections
    
    # Skip-connection with 4 and upsample7
    comb_layer1 = tf.add(layer4, upsample7)

    # Upsample combined layer 4+7
    upsample4_7 = tf.layers.conv2d_transpose(comb_layer1, num_classes, 4, 2, 'SAME',
                                            kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    
    # Skip-connection with 3 and upsample4_7
    comb_layer2 = tf.add(layer3, upsample4_7)

    # Upsample to original image
    upsample3_4_7 = tf.layers.conv2d_transpose(comb_layer2, num_classes, 16, 8, 'SAME',
                                              kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    '''
    print(layer7.get_shape)
    print(layer4.shape)
    print(layer3.shape)
    print(upsample7.shape)
    print(comb_layer1.shape)
    print(upsample4_7.shape)
    print(comb_layer2.shape)
    print(upsample3_4_7.shape)
    '''

    return upsample3_4_7
    
    #return output_layer
tests.test_layers(layers)


# In[5]:

def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function
    
    reshaped_logits = tf.reshape(nn_last_layer, (-1, num_classes))
    
    reshaped_labels = tf.reshape(correct_label, (-1, num_classes))
    
    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits = reshaped_logits, labels = reshaped_labels))
    
    # TODO_mine: Consider adding beta
    train_op = tf.train.AdamOptimizer(learning_rate).minimize(cross_entropy_loss)
    
    return reshaped_logits, train_op, cross_entropy_loss
tests.test_optimize(optimize)


# In[6]:

def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function
    idx = 0
    for epoch in range(epochs):
        for image, gt_image in get_batches_fn(batch_size):
            idx += 1
            _, loss = sess.run([train_op, cross_entropy_loss], 
                                     feed_dict = {input_image: image, correct_label: gt_image, 
                                                  keep_prob: 0.80, learning_rate: 0.00005})
            print(idx)
            if idx % 2 == 0: 
                print("Epoch {}/{}...".format(epoch, epochs),
                      "Training Loss: {:.4f}...".format(loss))
tests.test_train_nn(train_nn)


# In[7]:

def run():
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)
    epochs = 5 # With Batch_size == 2, epochs more than 6 throws OOM error. Even on p2 instance :(
    batch_size = 2

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        vgg_path = './data/vgg'
        image_input, keep_prob, layer3_out, layer4_out, layer7_out = load_vgg(sess, vgg_path)
        
        output_layer = layers(layer3_out, layer4_out, layer7_out, num_classes)
        
        learning_rate = tf.placeholder(dtype = tf.float32)
        correct_label = tf.placeholder(dtype = tf.float32, shape = (None, None, None, num_classes)) # 4-D tensor, project_tests.py
        
        
        reshaped_logits, train_op, cross_entropy_loss = optimize(output_layer, correct_label, learning_rate, num_classes)
        
        

        # TODO: Train NN using the train_nn function
        sess.run(tf.global_variables_initializer())
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, 
                 image_input, correct_label, keep_prob, learning_rate)

        # TODO: Save inference data using helper.save_inference_samples
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, reshaped_logits, keep_prob, image_input)


# In[8]:

if __name__ == '__main__':
    run()


# In[ ]:

import glob
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
get_ipython().magic('matplotlib inline')

### Load Images
images = glob.glob('./runs/*/*.png')
image = plt.imread(images[55])
plt.imshow(image)

