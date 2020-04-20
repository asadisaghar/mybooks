import pandas as pd
import googleapiclient as gapi
from googleapiclient.discovery import build
import requests
from requests_html import HTMLSession
from time import sleep

def cleanData(df):
    to_keep = ['Book Id', 'Title', 'Author',
               'ISBN', 'ISBN13', 'My Rating', 'Average Rating', 'Publisher',
               'Number of Pages', 'Year Published', 'Original Publication Year',
               'Date Read', 'Date Added', 'Bookshelves',
               'Exclusive Shelf',
               'Read Count']
    all_columns = list(df.columns)
    to_drop = list(set(all_columns) - set(to_keep))
    df.drop(columns=to_drop, inplace=True)
    columns = list(df.columns)
    columns = [x.replace(' ', '_') for x in columns]
    df.columns = columns
    df['Date_Read'] = pd.to_datetime(df['Date_Read'])
    df['ISBN13'] = df['ISBN13'].apply(lambda x: x.replace("=",""))
    df['ISBN13'] = df['ISBN13'].apply(lambda x: x.replace('"',""))
    df['ISBN13'] = pd.to_numeric(df['ISBN13'], errors='coerce')
    df['ISBN13'].fillna(0, inplace=True)
    df['ISBN13'] = df['ISBN13'].astype('int')

    return df

def searchGoogle(identifier, idtype):
    #9780385534635
    if identifier == 0:
        return []
    else:
        print(identifier)
        url = 'https://www.googleapis.com/books/v1/volumes?q={}+{}'.format(identifier, idtype.lower())
        res = requests.get(url).json()
        books = []
        if 'items' in res:
            for book in res['items']:
                books.append(book['volumeInfo'])
                print(book['volumeInfo']['title'], book['volumeInfo']['categories'])
        return books

def getBookURL(ISBN):
    sleep(1)
    url = "https://www.goodreads.com/search?utf8=%E2%9C%93&query={}".format(ISBN)
    r = requests.get(url)
    return r.url

def getGenre(url, cssSelector='.actionLinkLite.bookPageGenreLink'):
    session = HTMLSession()
    genres = {}
    r = session.get(url)
    doms = r.html.find(cssSelector)
    for dom in doms:
        if 'title' in dom.attrs:
            genre = dom.attrs['href'].replace('/shelf/users/{}?shelf='.format(url.split('/')[-1]),'')
            votes = int(dom.attrs['title'][:dom.attrs['title'].find(' people shelved this book as ')])
            genres[genre] = votes
    return genres

def getBookGenres(ISBN):
    book_url = getBookURL(ISBN)
    genres = getGenre(book_url)
    return list(genres.keys())
    
df = pd.read_csv('goodreads_library_export.csv')    
df = cleanData(df)
df['genres'] = df['ISBN13'].apply(lambda x: getBookGenres(x))

#make a column for genres
gs = df['genres'].values.tolist()
flat_gs = [item for sublist in gs for item in sublist]
unique_gs = list(set(flat_gs))

#make a new entry for each genre the bok is categorized in
df = df.explode('genres')
df = df.explode('Bookshelves')

df.to_pickle('goodreads_genres.pkl')
