# Software License Agreement (BSD License)
# Based on Phil Arkwright DGA Detection
# Modified to comply with modern framework
# Using Machine Learning
# All rights reserved.

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import glob
import joblib

# Step 1: Data Preparation
dga_folder = 'dataset/DGA-families'

# Load DGA domains from CSV files in the folder
dga_domains = []
for file_path in glob.glob(dga_folder + '*.csv'):
    df = pd.read_csv(file_path)
    dga_domains.extend(df['domain'].tolist())

# Load legitimate domains from CSV file
legitimate_file = 'dataset/majestic_onemillion/majestic_million.csv'
legitimate_data = pd.read_csv(legitimate_file)
legitimate_domains = legitimate_data['Domain'].tolist()

# Create the combined dataset with labels
domains = dga_domains + legitimate_domains
labels = ['dga'] * len(dga_domains) + ['legitimate'] * len(legitimate_domains)

# Step 2: Feature Extraction - Bigram Frequency Analysis
vectorizer = CountVectorizer(ngram_range=(2, 2), analyzer='char')
feature_matrix = vectorizer.fit_transform(domains)

# Step 3: Split the Dataset
X_train, X_test, y_train, y_test = train_test_split(
    feature_matrix, labels, test_size=0.2, random_state=42)

# Step 4: Train the Machine Learning Model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Step 5: Model Evaluation
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, pos_label='dga')
recall = recall_score(y_test, y_pred, pos_label='dga')
f1 = f1_score(y_test, y_pred, pos_label='dga')

print("Accuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1 Score:", f1)

# Save the model
joblib.dump(model, 'domain_classifier_model.pkl')

# Example Usage with Pi-hole
def classify_domain(domain):
    # Convert the domain into feature vector using the same vectorizer
    domain_vector = vectorizer.transform([domain])

    # Make predictions using the trained model
    prediction = model.predict(domain_vector)

    return prediction[0]  # Return the predicted class ('dga' or 'legitimate')
