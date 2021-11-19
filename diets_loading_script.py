import psycopg2
import json
import psycopg2.extras
import sys

con = psycopg2.connect(database='nutree') 

with open('diets.json', 'r') as d:
    data = json.load(d)



for i in data:
    cur = con.cursor() 
    q = "INSERT INTO diet VALUES(%(id)s, %(name)s, %(description)s)" 
    cur.execute(q, i)
    con.commit() 
    