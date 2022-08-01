# dependency modules for NLP
from nltk.tag.perceptron import PerceptronTagger
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import word_tokenize 
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk import pos_tag
import re

# dependency modules for NER Model
from pprint import pprint
import en_core_web_sm

# dependency modules for Spell Checker
from symspellpy import Verbosity

# dependency modules (common)
from ast import literal_eval

class query_processing:
    
    def __init__(self):
        
        self.date_dict = {'january':'01','february':'02','march':'03','april':'04','may':'05','june':'06','july':'07',
                          'august':'08','september':'09','october':'10','november':'11','december':'12'}
        
        self.custom_mapping = {'greater':1,'higher':1,'more':1,'highest':1,'more':1,'above':1,'beyond':1,'lower':0,'lowest':0,'less':0,'lesser':0,
                               'below':0,'until':0,'between':2,'no':11,'not':11,"dont":11,"don t":11,'never':11,'exclude':11,'besides':11,'excluding':11,
                               'except':11,'opposite':11,'J':'a','V':'v','N':'n','R':'r','01':0,'10':1,'02':2,'20':3,'03':4,'30':5,}
        
        self.customize_dict = {'new':'01','latest':'01','late':'01','current':'01','fresh':'01','modern':'01','present':'01','updat':'01','newest':'01',
                               'trendi':'01','now':'01','stale':'10','best':'02','finest':'02','greatest':'02','top':'02','foremost':'02',
                               'topmost':'02','lead':'02','preemin':'02','premier':'02','prime':'02','first':'02','chief':'02','princip':'02',
                               'suprem':'02','qualiti':'02','highest':'02','superl':'02','least':'20','worst':'20','bottom':'20','coars':'20',
                               'luxuri':'03','opul':'03','sumptuou':'03','affluent':'03','expens':'03','rich':'03','costli':'03','delux':'03',
                               'lush':'03','grand':'03','palati':'03','splendid':'03','magnific':'03','lavish':'03','extravag':'03','ornat':'03',
                               'fanci':'03','stylish':'03','eleg':'03','plush':'03','posh':'03','upmarket':'03','classi':'03','ritzi':'03','swanki':'03',
                               'upscal':'03','swish':'03','swank':'03','inexpens':'30','low':'30','econom':'30','competit':'30','afford':'30','reason':'30',
                               'budget':'30','economi':'30','cheap':'30','bargain':'30','cut':'30','half':'30','reduc':'30','discount':'30','middl':'30',
                               'averag':'30','standard':'30','mid':'30','usual':'30','mean':'30'}
        
        self.ignore = ['title','description','categori','details','price','brand','dollar','high','low','releas','great','list','follow','includ']
        self.accept = ['NN','NNS','RB','VB','VBP','VBD','VBG','VBZ','JJ','CD']
        self.stopwords = stopwords.words('english')
        self.ignore.extend(self.date_dict.keys())
        self.lemmatizer = WordNetLemmatizer()
        self.tagger = PerceptronTagger()
        self.stemmer = PorterStemmer()

    ########## Text Processing Functions #############
    
    def tokenization(self,text):
        return word_tokenize(text) 
    
    def strict_search(self,words):
        fields,advance_search = ['category:','brand:'],[]
        for i in range(0,len(words)):
            if fields[0]==words[i]:
                advance_search.append("{'match': {'main_cat': '"+' '.join(words[i+1:i+4])+"'}},")
            if fields[1]==words[i]:
                advance_search.append("{'match': {'brand': '"+' '.join(words[i+1:i+2])+"'}},")
        return advance_search

    def rm_punctuations(self,list_seq):
        punctuations= re.compile(r'[!"#%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~]')
        return [punctuations.sub(' ',words) for words in list_seq if punctuations.sub(' ',words)!= ' ' ]
    
    def spell_check(self,text,symspell,edit_dist=2):
        # store sent # reduce lengthening # check if numeric
        check_sent,pattern_1,pattern_2 = [], re.compile(r"(.)\1{2,}"), re.compile(r"\ *\$*\d+\$*$|^\$*\d+\$*\ +\$*\d*\$*\ *$")
        for word in text: 
            shorten = pattern_1.sub(r"\1\1", word)
            if re.search(pattern_2,shorten):
                check_sent.append(shorten)
            else:     
                # word correction
                if len(shorten)>1 or shorten=='$':
                    correction = symspell.lookup(shorten, Verbosity.CLOSEST, max_edit_distance=edit_dist,ignore_token=r"[$]+")
                    check_sent.append(str(correction[0]).split(',')[0]) if correction != [] else check_sent.append(shorten)
                else:
                     check_sent.append(shorten)
        return check_sent

    def POS_tag(self,list_seq):
        return pos_tag(list_seq)
    
    def track_negation(self,word):
        return 1  if self.custom_mapping.get(word) == 11 else 0
    
    def track_comparative(self,word,pos):
        if pos in ['JJR','JJS','RBR','IN']:
            return self.custom_mapping.get(word)
        
    def track_conditions(self,pos_tokens):
        cprt,neg = [],[]
        for w,pos in pos_tokens:
            neg.append(self.track_negation(w))
            cprt.append(self.track_comparative(w,pos))
        return cprt,neg
        
    def stemming(self,list_seq):
        return [self.stemmer.stem(word) for word in list_seq]
        
    def lemmatization(self,list_seq):
        lemmalist = []
        for word in list_seq:
            wn_pos = self.custom_mapping.get(self.tagger.tag([word])[0][1][0])
            lemmalist.append(self.lemmatizer.lemmatize(word,pos=wn_pos)) if wn_pos != None else lemmalist.append(word)
        return lemmalist
    
    def rm_stop_words(self,list_seq,excpt=[],neg=None,cond=None):
        temp,idx,c = [],[],0
        for word in list_seq:
            if word.lower() not in self.stopwords or word.lower() in excpt:  
                temp.append(word)
                idx.append(c)
            else:
                if neg!=None:
                    if neg[c]!=0:
                        temp.append(word)
                        idx.append(c)
                if cond!=None:
                    if cond[c]!=None:
                        temp.append(word)
                        idx.append(c)
            c+=1
        return temp,idx
    
    ########## Additional Processing Functions #############
    
    def check_conditions(self,condition):
        print(condition)
        if condition==0:
            sign = '<'
        elif condition==1:
            sign = '>'
        elif condition==2:
            sign = '<==>'
        elif condition==3:
            sign = '!<==>'
        elif condition==4:
            sign = '!='
        return sign
    
    def check_negations(self,neg_idx,words,tags,cond,ind):
        excluded,antonyms,w_len = [],[],len(words)
        for n in neg_idx:
            while n+1<w_len:
                w = words[n+1]
                lem = self.lemmatization(self.stemming([w]))[0]
                if lem not in self.ignore or self.custom_mapping.get(w)!=None:
                    temp = self.customize_dict.get(lem)
                    if cond[n+1]!=None:
                        if cond[n+1]==0:
                            cond[n+1]=1
                        elif cond[n+1]==1:
                            cond[n+1]=0
                        elif cond[n+1]==2:
                            cond[n+1]=3
                        elif cond[n+1]==3:
                            cond[n+1]=2
                    elif w == 'equal':
                        cond[n+1]=4
                    elif temp != None:
                        value = temp
                        value = value[1]+value[0]
                        ind[self.custom_mapping.get(value)] = 1
                        for k,v in self.customize_dict.items():
                            if v == value:
                                antonyms.append(k)    
                    else:
                        for syn in wordnet.synsets(w):
                            for l in syn.lemmas():
                                if l.antonyms():
                                    antonyms.append(l.antonyms()[0].name())
                    excluded.append(w)
                    if n+2<w_len and tags[n+1] in ['NN','NNS'] and self.customize_dict.get(w)==None:
                        if tags[n+2] in ['NN','NNS']:
                            n+=1
                            continue
                        else:
                            break
                    else:
                        break
                else:
                    excluded.append(w)
                n+=1   
        return excluded,set(antonyms),cond,ind
    
    def add_conditions(self,idx_prices,conditions):
        signs = []
        for idx in idx_prices:
            dec=idx
            while dec>=0:
                if conditions[dec] in [0,1,2,3,4]:
                    
                    if conditions[dec]==0:
                        signs.append(self.check_conditions(0))
                        conditions.pop(dec)
                        break
                    elif conditions[dec]==1:
                        signs.append(self.check_conditions(1))
                        conditions.pop(dec)
                        break
                    elif conditions[dec]==2:
                        signs.append(self.check_conditions(2))
                        conditions.pop(dec)
                        break
                    elif conditions[dec]==3:
                        signs.append(self.check_conditions(3))
                        conditions.pop(dec)
                        break
                    elif conditions[dec]==4:
                        signs.append(self.check_conditions(4))
                        conditions.pop(dec)
                        break
                if dec==0:
                    signs.append('==')
                dec-=1
        return signs
    
    def remove_val(self,to_keep,to_remove):
        for rm in to_remove:
            try:
                while True:
                    to_keep.remove(rm)
            except ValueError:
                pass
        return to_keep
    
    def remove_val2(self,l1,cats):
        temp,temp2 = [],cats.copy()
        temp2.extend(['time','video'])
        for i in l1:
            if self.customize_dict.get(i)==None and i not in temp2:
                temp.append(i)
        return temp
    
    def remove_idx(self,list_seq,to_keep_idx):
        return [list_seq[x] for x in to_keep_idx]
    
    def pos_tok_val(self,pos_tokens,idx=None):
        if idx!=None:
            val = [pos_tokens[x][0]  for x in idx]
        else:
            val = [x[0] for x in pos_tokens]
        return val
    
    def pos_tok_tag(self,pos_tokens,idx=None):
        if idx!=None:
            tags = [pos_tokens[x][1]  for x in idx]
        else:
            tags = [x[1] for x in pos_tokens]
        return tags
        
    def get_indices(self,list_seq,equal):
        indices,c = [],0
        for l in list_seq:
            if l in equal:
                indices.append(c)
            c+=1
        return indices
    
    def get_synonyms(self,words,tags,excluded,ind):
        synonyms,c = [],0
        for w in excluded:
            try:
                idx = words.index(w)
                words.pop(idx)
                tags.pop(idx)
            except ValueError:
                pass
        for tag in tags:
            if tag not in ['CD','CC']:
                if words[c] not in self.ignore:
                    temp = self.customize_dict.get(self.lemmatization(self.stemming([words[c]]))[0])
                    if temp != None:
                        value = temp
                        ind[self.custom_mapping.get(value)] = 1
                        for k,v in self.customize_dict.items():
                            if v == value:
                                synonyms.append(k)   
                    else:
                        for syn in wordnet.synsets(words[c]):
                            for l in syn.lemmas():
                                synonyms.append(l.name())
            c+=1
        return set(synonyms),ind
    
    ########## Text Extraction Functions #############
    
    def get_title_desc_brand(self,words,tags,orig_words):
        temp,temp2,c = [],[],0
        for tag in tags:
            if tag in self.accept:
                if words[c] not in self.ignore:
                    if self.custom_mapping.get(words[c])!=11:
                        temp.append(words[c])
                    if tag in ['NN','NNS','RB','CD']:
                        if self.custom_mapping.get(words[c])!=11:
                            temp2.append(words[c])
            c+=1
        return temp,temp2
    
    def get_date_price(self,doc):
        date,price = [],[]
        if doc != []:
            for x in doc.ents:
                if 'MONEY' == x.label_:
                    valid = True
                    for w in x.text.split():
                        if w.isalnum() and not w.isalpha() and not w.isdigit():
                            valid = False
                            break
                    if valid:
                        price.extend(re.findall(r"[-+]?(?:\d*\.\d+|\d+)",x.text))
                elif 'DATE' == x.label_:   
                    date.extend(re.findall(r"[-+]?(?:\d*\.\d+|\d+)",x.text))
                    for x in x.text.split():
                        if x in self.date_dict.keys():
                            date.append(x)
            return date, price
        else:
            return date, price
        
    def get_main_cats(self,words,tags,main_cats):
        m_cat,c = [],0
        ignore = ['video']
        for tag in tags:
            if tag in self.accept:
                if words[c] in main_cats and self.customize_dict.get(words[c])==None:
                    if words[c] not in ignore:
                        m_cat.append(words[c])
            c+=1
        return m_cat
    
    ########## Text Preprocessing #############
    
    def text_processing(self,text,dictionary):
        
        # tokenization
        word_tokens = self.tokenization(text)
        print('Tokenization\n',word_tokens)
        
        # advance search
        strict_conditions = self.strict_search(text.split())
        
        # remove punctuations
        clean_tokens = self.rm_punctuations(list_seq=word_tokens)
        print('\nRemove Punctuations\n',clean_tokens)
        
        # spell check
        check_tokens = self.spell_check(clean_tokens,symspell=dictionary)
        print('\nSpell Check\n',check_tokens)
        
        # POS tagging
        pos_tokens = self.POS_tag(clean_tokens)
        print('\nPOS text\n',pos_tokens)

        # negation & condition track
        conditions,negations = self.track_conditions(pos_tokens)
        print('\nCondition & Negation Idx Track')
        print('Conditions:',conditions,'\nNegations:',negations)
        
        # stemming
        stem_tokens = self.stemming(list_seq=self.pos_tok_val(pos_tokens))
        print('\nStemming\n',stem_tokens)
        
        # lemmatization
        lem_tokens = self.lemmatization(list_seq=stem_tokens)
        print('\nLemmatization\n',lem_tokens)

        # remove stopwords except negations
        filt_tokens,rs_idx = self.rm_stop_words(lem_tokens,[],negations)
        print('\nStop Words Removal except negations & comparatives\n',filt_tokens)
        
        # final POS tags
        filt_tags = self.pos_tok_tag(pos_tokens,rs_idx)
        
        # for ner model
        ner_text,_ = self.rm_stop_words(lem_tokens,['to','or','and'])
        
        # orig tokens copy
        orig_tokens,orig_rs_idx = self.rm_stop_words(self.pos_tok_val(pos_tokens),[],negations,conditions)
        orig_tags = self.pos_tok_tag(pos_tokens,orig_rs_idx)

        # realign conditions & negations
        conditions = self.remove_idx(conditions,orig_rs_idx)
        negations = self.remove_idx(negations,orig_rs_idx)
        
        return filt_tokens,filt_tags,ner_text,orig_tokens,orig_tags,conditions,strict_conditions,negations
    
    ########## NER Model #############
    def ner_model(self,text,nlp=en_core_web_sm.load()):
        doc = nlp(text)
        print('\nNER MODEL')
        pprint([(X.text, X.label_) for X in doc.ents])
        return doc 

    ########## ElasticSearch Query Functions #############
    
    def transdate(self,date):
        d,m,y = '01','01','2023'
        for x in date:
            if x in self.date_dict.keys():
                m = self.date_dict.get(x)
            elif len(x)<=2:
                d = x
            elif len(x)==4:
                y = x
        return y+'-'+m+'-'+d
    
    def get_range_price(self,price):
        if type(price)==list:
            _min,_max = min(price),max(price)
            if _min!=_max:
                return [_min,_max]
            else:
                return [0,_max]
        else:    
            return [(price*0.7),(price*1.3)]
        
    def assign_values(self,query,grth,lsth,range_prices):
        q,b,f,r,p='query','bool','filter','range','price'
        gt,lt,gte,lte='gt','lt','gte','lte'
        query[q][b][f][1][r][p][gt] = grth
        query[q][b][f][2][r][p][lt] = lsth
        query[q][b][f][3][r][p][gte] = range_prices[0]
        query[q][b][f][3][r][p][lte] = range_prices[1]
        return query
    
    def validate_conditions(self,price,signs):
        grth,lsth,range_prices = None,None,[None,None]
        c_grth,c_lsth,c = 0,0,0
        if price!=[]:
            price = list(map(float, price))
            if '<==>' in signs:
                range_prices = self.get_range_price(price)
            elif '!<==>' in signs:
                range_prices = self.get_range_price(price)
                range_prices = range_prices[1],range_prices[0]
            elif len(price)>1 and all(x=='==' for x in signs):
                range_prices = self.get_range_price(price)       
            else:
                for p in price:
                    if signs[c] in ['<','!=']:
                        if lsth==None:
                            lsth = p
                            c_lsth = p
                        else:
                            if p<c_lsth:
                                lsth = p
                                c_lsth = p
                    elif signs[c] in ['>']:
                        if grth==None:
                            grth = p
                            c_grth = p
                        else:
                            if p>c_grth:
                                grth = p
                                c_grth = p
                    elif signs[c] in ['=='] and len(price)==1:
                        range_prices = self.get_range_price(p)
                    c+=1                
        return grth,lsth,range_prices
    
    ########## ElasticSearch Query #############
    
    def create_esearch_query(self,general_query,gq_unique,orig_gq,excluded,price,date,cats,signs,strict_conditions):
        grth,lsth,range_prices = self.validate_conditions(price,signs)
        date,dynamic_strict_conditions = self.transdate(date),''
        min_should_match,operator = '3','and'
        if cats != [] and general_query == []:
            gq_unique = cats.copy()
            min_should_match = '1'
        elif cats != []:
            min_should_match = '4'
        if len(gq_unique)>4:
            operator = 'or'
        if len(gq_unique)==0:
            min_should_match = '3'
        general_query,gq_unique,orig_gq,cats,excluded = ' '.join(general_query),' '.join(gq_unique),' '.join(orig_gq),' '.join(cats),' '.join(excluded)
        if strict_conditions:
            all_cond = ''
            for cond in strict_conditions:
                all_cond += cond
            dynamic_strict_conditions = "'must' : ["+all_cond+"],"
        query = "{\
            'size': 500,\
            'query': {\
                'bool': {\
                'minimum_should_match':'"+min_should_match+"',\
                'should': [\
                    {'multi_match':{'query': '"+gq_unique+"','type': 'cross_fields','fields': ['title^5','desc^2','asin','brand'],'operator':'"+operator+"'}},\
                    {'multi_match':{'query': '"+general_query+"','type': 'best_fields','fields': ['title','desc','asin','brand','main_cat'],'operator':'or'}},\
                    {'multi_match':{'query': '"+orig_gq+"','type': 'cross_fields','fields': ['title^2','asin','brand'],'operator':'or'}},\
                    {'multi_match':{'query': '"+orig_gq+"','type': 'phrase','fields': ['title^5','desc^5']}},\
                    {'match':{'main_cat':'"+cats+"'}},\
                ],\
                "+dynamic_strict_conditions+"\
                'must_not' : [{'multi_match':{'query': '"+excluded+"','fields': ['title','desc','asin','brand','main_cat']}}],\
                'filter': [\
                    {'range':{'date':{'lte': '"+date+"'}}},\
                    {'range':{'price':{'gt': 'grth'}}},\
                    {'range':{'price':{'lt': 'lsth'}}},\
                    {'range':{'price':{'gte': 'range_prices[0]','lte': 'range_prices[1]'}}}\
                ]\
                    }\
                }\
            }"
        query = literal_eval(query)
        query = self.assign_values(query,grth,lsth,range_prices)
        return query

    def create_esearch_query2(self,sort_field,order,size):
        query = "{\
            'from': 0,\
            'size': '"+size+"',\
            'query': {\
                'match_all':{}\
            },'sort' : [\
                {'"+sort_field+"' : {'order' : '"+order+"'}}\
            ]}"
        query = literal_eval(query)
        return query
    
    ########## Ranking #############
    
    def to_integer(self,dt_time):
        return int(''.join(dt_time))
    
    def re_scale(self,value,_min,_max,new_min,new_max):
        delta1 = _max - _min
        if delta1==0:
            return 1
        else:
            delta2 = new_max - new_min
            return (delta2 * (value - _min) / delta1) + new_min
        
    def ranking_layer(self,ind,rs):
        prices,ranks,ratings,dates = [],[],[],[]
        new_min,new_max = 1,2
        for r in rs['hits']['hits']:
            prices.append(r['_source']['price'])
            ranks.append(r['_source']['rank'])
            ratings.append(r['_source']['rating'])
            dates.append(self.to_integer(r['_source']['date'].split('-')))
        if prices != []:
            p_min,p_max = min(prices),max(prices)
        if ranks != []:
            r_min,r_max = min(ranks),max(ranks)
        if dates != []:
            d_min,d_max = min(dates),max(dates)
        if ratings != []:
            rt_min,rt_max = min(ratings),max(ratings)

        items = rs['hits']['hits']

        for i in range(0,len(items)):
            score,price,rank,date = items[i]['_score'],items[i]['_source']['price'],items[i]['_source']['rank'],self.to_integer(items[i]['_source']['date'].split('-'))
            rating = items[i]['_source']['rating']
            if ind[0] == 1:
                date = self.re_scale(date,d_min,d_max,new_min,new_max)
                items[i]['_score'] = score*date
            elif ind[1] == 1:
                date = self.re_scale(date,d_min,d_max,new_min,new_max)
                date = (new_max+.1)-date
                items[i]['_score']  = score*date
            if ind[2] == 1:
                if rating==0:
                    rank = self.re_scale(rank,r_min,r_max,new_min,new_max)
                    rank = (new_max+.1)-rank
                    items[i]['_score'] = score*rank
                else:
                    rank = self.re_scale(rank,r_min,r_max,new_min,new_max)
                    rank = (new_max+.1)-rank
                    rating =  self.re_scale(rating,rt_min,rt_max,new_min,new_max)
                    items[i]['_score'] = score*rank*rating
            elif ind[3] == 1:
                if rating==0:
                    rank = self.re_scale(rank,r_min,r_max,new_min,new_max)
                    items[i]['_score'] = score*rank
                else:
                    rank = self.re_scale(rank,r_min,r_max,new_min,new_max)
                    rating =  self.re_scale(rating,rt_min,rt_max,new_min,new_max)
                    rating = (new_max+.1)-rating
                    items[i]['_score'] = score*rank*rating
            if ind[4] == 1:
                price = self.re_scale(price,p_min,p_max,new_min,new_max)
                items[i]['_score'] = score*price
            elif ind[5] == 1:
                price = self.re_scale(price,p_min,p_max,new_min,new_max)
                price = (new_max+.1)-price
                items[i]['_score']  = score*price

        re_ranked_items = sorted(items,key=lambda d: d['_score'],reverse=True)
        
        return re_ranked_items