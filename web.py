# dependency modules for web development (Flask)
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_session import Session
from flask_wtf import FlaskForm

# dependency modules for Database (ES)
from elasticsearch import Elasticsearch

# dependency modules for Spell Checker
from symspellpy import SymSpell

# dependecy modules (trie,qprocessing)
from qprocessing import query_processing
from trie import Trie

# dependency modules (common)
from math import ceil
import pickle
import time
import gc

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'kinggreysecretkey'
Session(app)

class fetch_data:

    def __init__(self,):
        self.my_symspell = SymSpell()

    def load_dict(self,filename):
        self.my_symspell.load_pickle(filename)
        return self.my_symspell
    
    def load_pickle(self,filename):
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        return data

    def set_iandp_count(self,items_c,page_n):
        session['items_c'] = items_c
        session['page_n'] = page_n
        session.modified = True

    def set_data(self,rs,total_hits,items_c,page_n,page_total,query):
        session['rs'] = rs
        session['query'] = query
        session['page_n'] = page_n
        session['items_c'] = items_c
        session['total_hits'] = total_hits
        session['page_total'] = page_total
        session.modified = True

    def get_data(self):
        if session.get('total_hits'):
            return session.get('rs'),session.get('total_hits'),session.get('items_c'),session.get('page_n'),session.get('query'),session.get('page_total')
        else:
            return [],0,0,0,session.get('query'),0

    def sorting(self,items):
        sort_type = session.get('sort')
        try:
            if sort_type=='rel':
                nlist = sorted(items,key=lambda d: d['_score'],reverse=True)
            elif sort_type=='top':
                nlist = sorted(items,key=lambda d: d['_source']['rank'])
            elif sort_type=='lat':
                nlist = sorted(items,key=lambda d: d['_source']['date'],reverse=True)
            return nlist
        except:
            return items

    def set_sort(self,sort_by):
        session['sort'] = sort_by
        session.modified = True
    
    def get_sort(self):
        return session.get('sort')

class SearchForm(FlaskForm):
    searched = StringField('Searched', validators=[DataRequired()])
    submit = SubmitField('Submit')

def search_query(query):
    if query!='':
        st = time.time()
        # text process query
        words,tags,ner_text,orig_words,orig_tags,conditions,strict_conditions,negations = query_class.text_processing(query, dictionary=custom_dict)
        
        # perform ner model
        text = ' '.join(ner_text)
        text = text.replace('$ ','$')
        doc = query_class.ner_model(text)

        # extract words to include in query
        general_query,gq_unique = query_class.get_title_desc_brand(words,tags,orig_words)
        cats = query_class.get_main_cats(words,tags,main_cats)
        date, price = query_class.get_date_price(doc)

        # indicators (use for ranking)
        indicate = [0,0,0,0,0,0]
        
        # negation
        neg_indices = query_class.get_indices(negations,[1])
        excluded, antonyms, conditions, indicate = query_class.check_negations(neg_indices,orig_words,orig_tags,conditions,indicate)
        
        # signs
        price_idx = query_class.get_indices(orig_words,price)
        signs = query_class.add_conditions(price_idx,conditions)
        print('\nAntonyms\n',antonyms)
        
        # remove dates & price in general query
        general_query = query_class.remove_val(general_query,date)
        general_query = query_class.remove_val(general_query,price)
        gq_unique = query_class.remove_val(gq_unique,date)
        gq_unique = query_class.remove_val(gq_unique,price)
        
        # get synonyms
        synonyms,indicate = query_class.get_synonyms(orig_words,orig_tags,excluded,indicate)
        print('\nSynonyms\n',synonyms)

        # preprocess negated words (antonyms)
        excluded = query_class.lemmatization(query_class.stemming(excluded))
        
        # remove negated words in general query
        general_query = query_class.remove_val(general_query,excluded)
        gq_unique = query_class.remove_val(gq_unique,excluded)
        
        # remove cats
        gq_unique = query_class.remove_val2(gq_unique,cats)
        
        print('\nGeneral Query Unique:\n',gq_unique)
        print('\nGeneral Query Original\n',general_query)
        orig_general_query = general_query.copy()

        # preprocess synonyms & antonyms
        further_meaning = synonyms | antonyms
        further_meaning = query_class.lemmatization(query_class.stemming(query_class.rm_punctuations(list(further_meaning))))
        general_query.extend(further_meaning)
        print('\nGeneral Query New\n',general_query)
        print('\nGeneral Excluded Words\n',excluded)
        
        # show extracted words according to attributes
        print('\nExtracted Words According To Attributes')
        date_text = ' '.join(date)
        price_text = ' '.join(price)
        category_text = ' '.join(cats)
        print('Date:',date_text)
        print('Price:',price_text)
        print('Category:',category_text)
        
        print('\nConditions\n',signs)
        
        # show advance search conditions
        print("\nAdvance Search Conditions:\n",strict_conditions,"\n")
        
        # create esearch query
        process_query = query_class.create_esearch_query(general_query,gq_unique,orig_general_query,excluded,price,date,cats,signs,strict_conditions)
        print('Process Query:', process_query)

        # querying
        rs = es.search(index='amazon',body=process_query,request_timeout=60)
        print('Query Done')

        end = time.time()
        print("Time Spent:",end-st)
        
        total_hits = rs['hits']['total']['value']

        new_rs = query_class.ranking_layer(indicate,rs)
        
        # set defualt values
        fetch.set_data(new_rs,total_hits,100,1,ceil(total_hits/100),query)

@app.before_first_request
def initialization():
    
    # global classes
    global query_class
    global fetch
    global t1
    global t2

    # global storage variables
    global custom_dict
    global main_cats
    global brands
    global es

    # resources path
    path = 'Data Preprocess Small Complete/resources/'
    
    # instantiate db class
    fetch = fetch_data()
    # instantiate trie class
    t1 = Trie(10,100)      
    t2 = Trie(1,100)
    # instantiate query processing class
    query_class = query_processing()

    # import custom dictionary
    custom_dict = fetch.load_dict(filename=path+'custom_dictionary.txt') 
    # custom_dict = SymSpell()
    
    # import main categories
    main_cats = fetch.load_pickle(filename=path+'main_cats.txt')
    # import brands
    brands = fetch.load_pickle(filename=path+'brands.txt')
    # import ngrams
    ngrams = fetch.load_pickle(filename=path+'ngrams_freq.txt')
    
    # form trie 
    t1.formTrie(ngrams.items(),min_len=2,max_len=3)
    t2.formTrie(ngrams.items(),max_len=1)
    for key in brands:
        t2.insert(key, 100)
    for key in main_cats:
        t2.insert(key, 100)

    seq = list(query_class.date_dict.keys())
    seq.extend(query_class.custom_mapping.keys())
    seq.extend(query_class.customize_dict.keys())
    seq.extend(query_class.stopwords)
    for key in seq:
        t2.insert(key, 100)
    
    # preprocess brands and main categories
    stem = query_class.stemming(main_cats)
    main_cats = query_class.lemmatization(stem)
    stem = query_class.stemming(brands)
    brands = query_class.lemmatization(stem)

    # elastic search configuation
    es = Elasticsearch(HOST='http://localhost', PORT=9200)
    
    # free up some memory space
    del ngrams
    del stem
    del seq
    gc.collect()
        
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

@app.route('/')
def index():
    return redirect('/home')

@app.route('/home')
def home():
    top_query = query_class.create_esearch_query2(sort_field='rank',order='asc',size='20')
    session['rs']  = es.search(index='amazon',body=top_query,request_timeout=60)
    session.modified=True
    top_items = session.get('rs')['hits']['hits']
    latest_query = query_class.create_esearch_query2(sort_field='date',order='desc',size='20')
    session['rs'] = es.search(index='amazon',body=latest_query,request_timeout=60)
    session.modified=True
    lat_items = session.get('rs')['hits']['hits']
    return render_template('home.html',top_prod=top_items,latest_prod=lat_items,searched='')

@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        search_words = form.searched.data
        search_query(query=search_words)
        items,_,_,page_n,query,page_total = fetch.get_data()
        items = items[0:100]
        fetch.set_sort('rel')
        items = fetch.sorting(items)
        return render_template('search.html',products=items,searched=query,page_num=page_n,page_total=page_total)
    else:
        fetch.set_data([],0,0,0,0,'')
        items,_,_,page_n,query,page_total = fetch.get_data()
        return render_template('search.html',products=items,page_num=page_n,searched=query,page_total=page_total)
    
@app.route('/processing', methods=['POST'])
def processing():
    if request.method == "POST":
        query = request.form.get('query')
        resp = t1.AutoSuggestions(query)
        if type(resp)==list:
            return jsonify(dict(autocomplete=resp))
        else:
            query = query.split()
            prev_query = ' '.join(query[:-1])
            resp = t2.AutoSuggestions(query[-1])
            resp = prev_query+' '+resp[0]
            return jsonify(dict(autocomplete=[resp]))
        
@app.route('/search_top')
def search_top():
    top_query = query_class.create_esearch_query2(sort_field='rank',order='asc',size='10000')
    top_results = es.search(index='amazon',body=top_query,request_timeout=60)
    total_hits = top_results['hits']['total']['value']
    fetch.set_data(top_results['hits']['hits'],total_hits,100,1,ceil(total_hits/100),'')
    items,_,_,page_n,query,page_total = fetch.get_data()
    fetch.set_sort('top')
    items = items[0:100]
    return render_template('search.html',products=items,searched=query,page_num=page_n,page_total=page_total)
    
@app.route('/search_latest')
def search_latest():
    lat_query = query_class.create_esearch_query2(sort_field='date',order='desc',size='10000')
    lat_results = es.search(index='amazon',body=lat_query,request_timeout=60)
    total_hits = lat_results['hits']['total']['value']
    fetch.set_data(lat_results['hits']['hits'],total_hits,100,1,ceil(total_hits/100),'')
    items,_,_,page_n,query,page_total = fetch.get_data()
    fetch.set_sort('lat')
    items = items[0:100]
    return render_template('search.html',products=items,searched=query,page_num=page_n,page_total=page_total)

@app.route('/search_shortcuts')
def search_shortcuts():
    items,total_hits,_,page_n,query,page_total = fetch.get_data()
    if total_hits!=0:
        items = items[0:100]
        fetch.set_sort('rel')
        items = fetch.sorting(items)
    return render_template('search.html',products=items,searched=query,page_num=page_n,page_total=page_total)

@app.route('/shortcuts', methods=['POST'])
def shortcuts():
    if request.method == "POST":
        query = request.form.get('query')
        search_query(query=query)
        return jsonify(dict(redirect=url_for('search_shortcuts')))

@app.route('/rel_prod')
def rel_prod():
    fetch.set_sort('rel')
    items,total_hits,_,page_n,query,page_total = fetch.get_data()
    if total_hits!=0:
        items = items[(page_n*100)-100:page_n*100]
        items = fetch.sorting(items)
    return render_template('search.html',products=items,searched=query,page_num=page_n,page_total=page_total)

@app.route('/lat_prod')
def lat_prod():
    fetch.set_sort('lat')
    items,total_hits,_,page_n,query,page_total = fetch.get_data()
    if total_hits!=0:
        items = items[(page_n*100)-100:page_n*100]
        items = fetch.sorting(items)
    return render_template('search.html',products=items,searched=query,page_num=page_n,page_total=page_total)

@app.route('/top_prod')
def top_prod():
    fetch.set_sort('top')
    items,total_hits,_,page_n,query,page_total = fetch.get_data()
    if total_hits!=0:
        items = items[(page_n*100)-100:page_n*100]
        items = fetch.sorting(items)
    return render_template('search.html',products=items,searched=query,page_num=page_n,page_total=page_total)

@app.route('/next')
def next_page():
    rs,total_hits,items_c,page_n,query,page_total = fetch.get_data()
    if total_hits!=0:
        if items_c<=total_hits and items_c%100==0:
            page_n+=1
            items_c+=100
            items = rs[items_c-100:items_c]
            if items_c>total_hits:
                items_c-=(items_c-total_hits)
            fetch.set_iandp_count(items_c,page_n)
            items = fetch.sorting(items)
            return render_template('search.html',products=items,page_num=page_n,searched=query,page_total=page_total)    
        else:
            items = rs[items_c-(items_c%100):items_c]
            items = fetch.sorting(items)
            return render_template('search.html',products=items,page_num=page_n,searched=query,page_total=page_total)
    else:
        return render_template('search.html',products=items,page_num=page_n,searched=query,page_total=page_total)

@app.route('/prev')
def prev_page():
    rs,total_hits,items_c,page_n,query,page_total = fetch.get_data()
    if total_hits!=0:
        if items_c>100 and items_c%100!=0:
            page_n-=1
            rmdr = items_c%100
            items_c-=(rmdr)
            items = rs[items_c-100:items_c]
            fetch.set_iandp_count(items_c,page_n)
            items = fetch.sorting(items)
            return render_template('search.html',products=items,page_num=page_n,searched=query,page_total=page_total)
        if items_c>100:
            page_n-=1
            items_c-=100
            items = rs[items_c-100:items_c]
            fetch.set_iandp_count(items_c,page_n)
            items = fetch.sorting(items)
            return render_template('search.html',products=items,page_num=page_n,searched=query,page_total=page_total)
        else:
            items = rs[items_c-100:items_c]
            items = fetch.sorting(items)
            return render_template('search.html',products=items,page_num=page_n,searched=query,page_total=page_total)
    else:
        return render_template('search.html',products=items,page_num=page_n,searched=query,page_total=page_total)

if __name__ == '__main__':
    app.run()