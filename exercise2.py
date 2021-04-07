# -*- coding: utf-8 -*-
"""Exercise2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1B64G5qdu8StpSmc9IfoU8FwX7vnvI0Ln

## Ερώτηση 2
"""

!pip install dask[dataframe]

"""Importing Libraries"""

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
import scipy.sparse as sp_sparse
from sklearn.model_selection import train_test_split
import sklearn.model_selection as model_selection
from google.colab import drive
from sklearn.metrics.pairwise import cosine_similarity
drive.mount('/content/gdrive')

"""Importing the datasets"""

business = pd.read_json('/content/gdrive/MyDrive/small/yelp_academic_dataset_business.json',encoding = 'utf8', lines=True)

business.head()

TorontoData = pd.DataFrame(columns = ['user_id', 'business_id', 'rating'])
dataToronto_bus = business.loc[business['city'] == 'Phoenix']
dataToronto_bus = dataToronto_bus.loc[dataToronto_bus['review_count'] >= 15]

dataToronto_bus.head()

import json
with open('/content/gdrive/MyDrive/small/yelp_academic_dataset_review.json') as f:
    user = pd.DataFrame(json.loads(line) for line in f)

print(len(user))
user.head()

import dask.dataframe as dd
step1 = dd.read_csv('/content/gdrive/MyDrive/pruned_data.csv', header=None)

"""# Βήμα 1"""

user1 = pd.DataFrame(columns = ['user_id','review_count_user'])
pruned_data = pd.DataFrame(columns = ['user_id', 'business_id', 'stars'])

user_num = user.value_counts(subset=['user_id'])

user_num = user_num.to_frame()

user_temp = user_num.index.values
user_ids = [i[0] for i in user_temp]

user1['user_id'] = user_ids
user1['review_count_user'] = user_num.iloc[:, -1].values

user1 = user1.loc[user1['review_count_user']>= 15]
temp = pd.merge(user, user1 , on = ['user_id'])

pruned_data['user_id'] = temp['user_id']
pruned_data['business_id'] = temp['business_id']
pruned_data['stars'] = temp['stars']

print(pruned_data)

"""# Βήμα 2

Create sparse matrix (R)
"""

counter_user = 0
counter_bus = 0

user_ids = {}
business_ids = {}

user_coords = []
business_coords = []

ratings = []

for index, row in step1.iterrows():
 
  if row[0] in user_ids :

    if row[1] in business_ids:
      continue
    else:
      business_ids[row[1]] = counter_bus
      business_coords.append(counter_bus)
      counter_bus += 1

      user_val = user_ids[row[0]]
      user_coords.append(user_val)

      ratings.append(row[2])

  else:
    user_ids[row[0]] = counter_user
    user_coords.append(counter_user)
    counter_user += 1

    if row[1] in business_ids:
      bus_val = business_ids[row[1]]
      business_coords.append(bus_val)
      ratings.append(row[2])
      
    else:
      business_ids[row[1]] = counter_bus
      business_coords.append(counter_bus)
      counter_bus += 1 

      ratings.append(row[2])
   
rows = np.array(user_coords) 
cols = np.array(business_coords)
data = np.array(ratings)
print(rows.size)
print(cols.size)
print(data.size)

# convert to sparse matrix representation 
R = csr_matrix((data, (rows, cols)),  shape = (rows.size, cols.size)).toarray()
print("Sparse matrix: \n",R)

X_train, X_test, y_train, y_test = model_selection.train_test_split(R, R, train_size=0.95,test_size=0.05, random_state=np.random)
print ("X_train: ", X_train) # the big part
print ("X_test: ", X_test) # the 5% part
x_test_nonzeros = np.nonzero(X_test)

"""Το x_train θα ειναι το μεγαλο μερος του αραιου πινακα που και το x_test θα ειναι το 5% του πινακα που θα αφαιρεθει ωστε να επιχειρισουμε να το πρροβλεψουμε με τους παρακατω υπολογισμου.

# Βήμα 3 -Item-Based Collaborative Filtering (ICF)

cosine similarity matrix
"""

cos_sim_users = cosine_similarity(X_test, Y=None)

sim_nonzeros = np.nonzero(cos_sim_users)
# print(sim_nonzeros)

array1 = x_test_nonzeros[0] # the users 
array2 = x_test_nonzeros[1] # the businesses

def predict(similarity_vector,ratings_vector):
  print(similarity_vector)
  print(ratings_vector)

  # calculate sum of user similarities for denominator
  user_sim_sum = np.sum(similarity_vector)
  # print(user_sim_sum)

  # calculate sum of the similarity vector multiplied by the ratings vector
  dot_vector = np.dot(similarity_vector,ratings_vector)
  big_sum = np.sum(dot_vector)
  print(big_sum)

  prediction = big_sum / user_sim_sum
  # print(prediction)

  return prediction

def ICF(k, array1, array2):
  user_list = []
  predictions = []

  for index in range(len(array1)):

    user = array1[index] # get position of user
    business = array2[index] # get position of business

    for index2 in range(len(array2)):

      if array2[index2] == business:
        user_index = array1[index2]
        user_list.append(X_test[user_index])

    user_vectors = np.array(user_list)
    non_zero_vectors = np.nonzero(user_vectors)


    ratings_of_b = []
    pos_x = non_zero_vectors[0]
    pos_y = non_zero_vectors[1]
    
    for x in pos_x:
      for y in pos_y:
        ratings_of_b.append(user_vectors[x,y])


    u = X_test[user]
    non_zero_user = np.nonzero(u)

    # user_vectors = user_vectors.reshape(-1, 1)
    # u = u.reshape(-1,1)
    num_of_vectors = np.size(user_vectors,0)

    if num_of_vectors == 1:
      continue

    cos_sim_vectors = cosine_similarity(user_vectors[0:1] , user_vectors[1:] , dense_output=True) 

    sorted_cos_sim = np.sort(cos_sim_vectors)[::-1]
    similarity_vector = sorted_cos_sim[:k]
  
    ratings_vector = ratings_of_b[:k]
    ratings_vector = np.array(ratings_vector)

    if similarity_vector.size != ratings_vector.size:
      continue

    rating_prediction = predict(similarity_vector,ratings_vector)
    predictions.append(rating_prediction)

    user_list.clear()

  return predictions

predictions = ICF(2,array1,array2)
print(predictions)

""" # Βήμα 4 - Item-Based Collaborative Filtering (ICF) with Inverse Matrix """

# create Inverse matrix

inverse = np.linalg.pinv(X_test)
print(inverse)

inverse_nonzeros = np.nonzero(inverse)
array1_inverse = inverse_nonzeros[0] # the users 
array2_inverse = inverse_nonzeros[1] # the businesses

predictions = ICF(2,array1_inverse,array2_inverse)

"""# Βήμα 5 - Singular Value Decomposition (SVD)"""

u, s, vh = np.linalg.svd(R, full_matrices=True)

k=20
rank_k = []

sorted_svd = np.sort(s)[::-1]
for i in range(20):
  rank_k.append(sorted_svd[i])