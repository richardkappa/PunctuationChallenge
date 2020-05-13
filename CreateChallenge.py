import ebooklib
import os
import nltk
import random
import pandas as pd
import string
from bs4 import BeautifulSoup
from ebooklib import epub
import numpy as np
from itertools import compress
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def epub2thtml(epub_path):
    book = epub.read_epub(epub_path)
    chapters = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item.get_content())
    return chapters
    
blacklist = [   '[document]',   'noscript', 'header',   'html', 'meta', 'head','input', 'script'  ]
# there may be more elements you don't want, such as "style", etc.

def chap2text(chap):
    output = ''
    soup = BeautifulSoup(chap, 'html.parser')
    text = soup.find_all(text=True)
    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)
    return output
    
def thtml2ttext(thtml):
    Output = []
    for html in thtml:
        text =  chap2text(html)
        Output.append(text)
    return Output
    
def epub2text(epub_path):
    chapters = epub2thtml(epub_path)
    ttext = thtml2ttext(chapters)
    return ttext
    
def extSentences(epub_path):
    theBook = epub2text(epub_path)
    Sentences = []
    for x in theBook:
        for w in nltk.sent_tokenize(x):
            Sentences.append(w)
    [item.rstrip('\r\n\xa0') for item in Sentences]
    return Sentences
    
#Remove carriage returns and other similar annoying bits
def remret(sent):
    no_punct = ""
    for char in sent:
            no_punct = no_punct + char
            no_punct = no_punct.rstrip('\r\n\xa0')
    return no_punct

#Create a list without punctuation
def removePunct(sent):
    punctuations = '''!‘()-[]{};:'"\,<>./?@#$%^&—*_~'''
    no_punct = ""
    for char in sent:
       if char not in punctuations:
            no_punct = no_punct + char
            no_punct = no_punct.rstrip('\r\n\xa0').replace('“', '').replace('”','').replace('’','').lower()
    return no_punct
    
def CleanBook(epub_path,NumberAnswers):  
    
    out=extSentences(epub_path)
    
    #Remove sentences that are too short and too long
    MinLength = np.vectorize(len)(out)>100
    MaxLength = np.vectorize(len)(out)<150

    CorrectLength = list(MinLength * MaxLength)

    out= list(compress(out, CorrectLength))
    
    #Remove the carriage returns and similar
    out_withP = []
    for x in out:
        out_withP = out_withP + [remret(x)]
        
    #Remove all punctuation and capitals
    out_noP = []
    for x in out_withP:
        out_noP = out_noP + [removePunct(x)]
        
    #ignore the first and last 20 sentences as these might not be part of the story
    randomlist = random.sample(range(20, len(out)-20), NumberAnswers)

    #Select the sentences we want to put in the output questions
    worksheet_OrigList = list( out_withP[i] for i in randomlist)
    worksheet_NoPunctList = list( out_noP[i] for i in randomlist)
    
    #Convert to a dataframe so they can be output in the next step
    Questions = pd.DataFrame(worksheet_NoPunctList,  columns =[''])
    Answers = pd.DataFrame(worksheet_OrigList, columns =[''])
    
    return Questions, Answers
    
def PrintQuestions(epub_path,NumberAnswers, OutPath, BookName):
    Questions, Answers =CleanBook(epub_path, NumberAnswers)
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("MyReport.html")
    template_vars = {"TheTitle" : BookName + " Punctuation Worksheet",
                     "Head1" : "Questions",
                     "Questions": Questions.to_html(),
                     "Head2" : "Answers",
                     "Answers": Answers.to_html(),
                     "book" : BookName}

    html_out = template.render(template_vars)
    HTML(string=html_out).write_pdf(OutPath,stylesheets=["style.css"])
    
def Export(book, NumberQuestions, rootPath):
    os.chdir(rootPath)
    Book_Location = os.path.join(rootPath,"Books/"+book+".epub")
    pdfname = book + " Punctuation Worksheet"
    Output_Location = "Worksheets/"+pdfname+".pdf"
    
    PrintQuestions(Book_Location,NumberQuestions, Output_Location, pdfname)
    
#Run the program
input_path = "/home/pi/Documents/Blog Post 1/"

Export("Treasure Island", 15, input_path)
