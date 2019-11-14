import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import re
import datetime
import warnings

os.chdir('N:\\Departments_hcb\\ГБ Финансовый блок\\Finance management\\Analyses\\Ad-hoc requests\\2019\\Cards statistics')


id_webpages = pd.read_csv('webpage ids.txt',header=None).iloc[:,0].values.astype(int)
data = pd.DataFrame({'publish_date':range(len(id_webpages)), 'id_webpage':0, 'soups':0})

df1_list = []

warnings.filterwarnings('ignore')
for i in range(len(id_webpages)):
    url = 'https://nationalbank.kz/document/?docid='+str(id_webpages[i])
    res = requests.get(url, verify=False)
    data['id_webpage'][i]=id_webpages[i]
    if res.status_code >=200 and res.status_code <300 and id_webpages[i]>=4904:
        soup = BeautifulSoup(res.content,'lxml')
        stat_date = datetime.datetime.strptime(re.search(r'(\d+/\d+/\d+)',soup.find('span').text).group(1),'%d/%m/%Y')
        data['publish_date'][i]=stat_date
        
        all_tables = pd.read_html(str(soup), thousands=' ', decimal=',')
        
        df1 = all_tables[1].copy(deep=True)
        df1['use']= 0
        df1['g0']=''
        df1['g1']=''
        df1['g2']=''
        g0 = ''
        g1 = ''
        g2 = ''
        
        for r in df1.itertuples():
            
            i=r[0]
            
            #main level operations
            if re.search('оличество', r[1]) is not None:
                
                #level 1
                if re.search('в.т.ч.', r[1]) is not None:
                    u=0
                elif re.search('(ед.)', r[1]) is not None:
                    u=1
                g0 = r[1]
                df1['use'][i]=u
            
            df1['g0'][i]=g0    
            
            #level 2 operations
            if re.search('истемы', r[1]) is not None or re.search('isa|aster', r[1]) is not None:
                
                #level 2
                if re.search('.т.ч.', r[1]) is not None or re.search('из них', r[1]) is not None:
                    if re.search('-', df1.iloc[i+1][0]) is None and re.search('isa|aster', r[1]) is not None:
                        df1['use'][i]=1
                    else:
                        df1['use'][i]=0
                else:
                    df1['use'][i]=1
                
                g1 = r[1]
                df1['g1'][i]=g1
            
            #level 3 manipulations
            if re.search('-', r[1]) is not None and re.search('оличество', r[1]) is None:
                #level 3
                df1['use'][i]=1
                
                if  re.search('карточ', df1['g0'][i]) is not None:
                    df1['g1'][i]=g1    
                
                df1['g2'][i]=r[1]
                
        date1 = str(df1.iloc[1,1]).replace('на','').strip()
        date2 = str(df1.iloc[1,2]).replace('на','').strip()
        
        if len(date1)<10:
            date1= datetime.datetime.strptime(date1,'%d.%m.%y') 
        else: date1= datetime.datetime.strptime(date1,'%d.%m.%Y') 
        
        if len(date2)<10:
            date2= datetime.datetime.strptime(date2,'%d.%m.%y') 
        else: date2= datetime.datetime.strptime(date2,'%d.%m.%Y') 
        
        df1.columns = ['t', date1, date2, 'use', 'g0', 'g1', 'g2']
        df1.drop([0,1],inplace= True)  #first two rows with unwanted table name
        df1.drop(df1[df1.use==0].index,  inplace = True)  #drop unused rows
        df1.drop(columns = ['use','t'], inplace=True)
        df1 = df1.set_index(['g0','g1','g2']).stack().reset_index().rename(index=str, columns={'level_3':'period', 0:'value'})
        
        df1_list.append(df1)  
    
    else: 
        data['publish_date'][i] = 'Error'

warnings.filterwarnings('ignore')


for i in range(len(df1_list)):
    if 'main_df' in globals():
        main_df = pd.concat([main_df,df1_list[i]])
    else:
        main_df=df1_list[i]

main_df['value'] = main_df['value'].apply(lambda x: float(x.replace('-','0').replace(u'\xa0', u'').replace(',','.').replace(' ','').strip()))
main_df.drop_duplicates(inplace=True)

main_df.to_excel('d.xlsx')

