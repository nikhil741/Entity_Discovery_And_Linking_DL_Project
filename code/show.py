'''#############################################################
Authors		: Bhiman Kumar Baghel	17CS60R74
			: Hussain Jagirdar 		17CS60R83
			: Lal Sridhar			17CS60R39
			: Nikhil Agarwal		17CS60R70
			: Shah Smit Ketankumar	17CS60R72
Usage		: Entity feature extraction
Data		: 13-04-2018 
#############################################################'''

import pickle
import tensorflow as tf
import pysolr
import source_xml_parser
import nltk
import numpy as np
from tensorflow.contrib import rnn

tf.set_random_seed(1234)

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

def get_features():
	
	data_dict = load_obj("../ere_dict_new/_entity_dict")

	xml_data = source_xml_parser.get_source()
	
	input_text = nltk.word_tokenize((xml_data.find('TEXT').get_text().replace(":"," ").replace("."," ").replace("("," ").replace(")"," ").replace("-"," ")).lower())
	

	solr = pysolr.Solr('http://localhost:8983/solr/glove', timeout=10)
	
	input_x_dict = dict()
	
	#One hot vector
	y_map = dict()
	y_map["PER"] = np.array([[1,0,0,0,0,0]])	
	y_map["ORG"] = np.array([[0,1,0,0,0,0]])
	y_map["GPE"] = np.array([[0,0,1,0,0,0]])
	y_map["LOC"] = np.array([[0,0,0,1,0,0]])
	y_map["FAC"] = np.array([[0,0,0,0,1,0]])
	y_map["OTH"] = np.array([[0,0,0,0,0,1]])

	y = list()
	x = list()

	for i in input_text:
		if i in data_dict:
			y.append(y_map[data_dict[i]])
		else:
			y.append(y_map["OTH"])
	
		results = solr.search('id:'+i)
		if(len(results)==0):
			print i
		for r in results:
			xx = np.array(r["vector"].split(" "))
			xx = xx.astype(float)
			x.append(xx)
	return x,y
	# print data_dict

def RNN(x, weights, biases, timesteps,num_hidden):

	# Prepare data shape to match `rnn` function requirements
	# Current data input shape: (batch_size, timesteps, n_input)
	# Required shape: 'timesteps' tensors list of shape (batch_size, n_input)

	# Unstack to get a list of 'timesteps' tensors of shape (batch_size, n_input)
	x = tf.unstack(x, timesteps, 1)

	# Define a lstm cell with tensorflow
	lstm_cell = rnn.BasicLSTMCell(num_hidden, forget_bias=1.0)

	# Get lstm cell output
	outputs, states = rnn.static_rnn(lstm_cell, x, dtype=tf.float32)

	# Linear activation, using rnn inner loop last output
	return tf.matmul(outputs[-1], weights['out']) + biases['out']

def main():
	x,y = get_features()
	# print x[0].shape
	# print (np.vstack(x)).shape
	# exit()
	learning_rate = 0.001
	training_steps = 64
	batch_size = 128
	display_step = 200

	num_input = len(x[0]) # MNIST data input (img shape: 28*28)
	timesteps = 1 # timesteps
	num_hidden = 100 # hidden layer num of features
	num_classes = 6
	batch_size = 1
	learning_rate = 0.0001

	X = tf.placeholder("float", [None, None, num_input])
	Y = tf.placeholder("float", [None,num_classes])

	weights = {
	    'out': tf.Variable(tf.random_normal([num_hidden,num_classes])),
	    
	}

	biases = {
	    'out': tf.Variable(tf.random_normal([num_classes]))
	}

	logits = RNN(X, weights, biases, timesteps,num_hidden)
	prediction = tf.nn.softmax(logits)

	loss_op = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=Y))
	optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate)
	train_op = optimizer.minimize(loss_op)

	correct_pred = tf.equal(tf.argmax(prediction, 1), tf.argmax(Y, 1))
	accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

	init = tf.global_variables_initializer()

	with tf.Session() as sess:

		# Run the initializer
		sess.run(init)

		for step in range(1, training_steps+1):
			temp_loss = 0
			acc = 0
			print "Epoche",step
			for i in range(len(x)):
				batch_x, batch_y = x[i],y[i]

				# Reshape data to get 28 seq of 28 elements
				batch_x = batch_x.reshape((batch_size, timesteps, num_input))
				# Run optimization op (backprop)
				sess.run(train_op, feed_dict={X: batch_x, Y: batch_y})
				loss = sess.run(loss_op, feed_dict={X: batch_x,Y: batch_y})
				temp_loss += loss

			batch_x = np.vstack(x).reshape((len(x), timesteps, num_input))
			print "Accuracy",sess.run(accuracy, feed_dict={X: batch_x,Y: np.vstack(y)})
			print("Step " + str(step) + ", Minibatch Loss= " + \
			"{:.4f}".format(temp_loss) + ", Training Accuracy= " + \
			"{:.3f}".format(acc))

		print("Optimization Finished!")

		# Calculate accuracy for 128 mnist test images


if __name__ == '__main__':
	main()