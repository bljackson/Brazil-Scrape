import requests
import codecs
import pandas as pd
from selenium import webdriver
import time
import urllib
import logging
import logging.handlers
import re
import os
import goslate
import traceback
import pdfminer
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO
import smtplib
from bs4 import BeautifulSoup
import sys
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')


try:
    class Brazil(object):

        def __init__(self,search,startDate,endDate,year):
            self.search = search
            self.startDate = startDate
            self.endDate = endDate
            self.year = year
            self.dataList = {'edicao.paginaAtual':'1','edicao.fonetica':'null','edicao.txtPesquisa':self.search,'edicao.dtInicio':self.startDate,'edicao.dtFim':self.endDate,'edicao.ano':self.year}
            self.r = requests.get('http://pesquisa.in.gov.br/imprensa/core/consulta.action')

            while True:
                try:
                    self.rPost = requests.post("http://pesquisa.in.gov.br/imprensa/core/consulta.action", data=self.dataList)
                    self.soup = BeautifulSoup(self.rPost.content, 'html.parser')
                    if "Proxy Error" in self.rPost.content or len(self.soup.find_all('a')) < 2:
                        print "Proxy Error or nothing"
                        self.r.Post = requests.post("http://pesquisa.in.gov.br/imprensa/core/consulta.action", data=self.dataList)
                        self.soup = BeautifulSoup(self.rPost.content, 'html.parser')
                    else:
                        break
                except:
                    print "in except. retry."

            self.soup = BeautifulSoup(self.rPost.content, 'html.parser')
            self.ultimo = ''
            self.linkList = []
            self.current_link = ''

            #self.DownloadPath = "C:/Users/Bethany/WorkWorkspace/BrazilTryAgainMoFo/"

            self.DownloadPath = "/home/scott/BrazilOutput/"

            try:
                os.mkdir(self.DownloadPath)
            except:
                pass
            try:
                os.mkdir(self.DownloadPath + self.search)
            except:
                pass
            try:
                os.mkdir(self.DownloadPath + self.search + "/" + self.year)
            except:
                pass
            try:
                os.mkdir(self.DownloadPath + self.search + "/" + self.year + "/pdfs/") 
            except:
                pass
            try:
                os.mkdir(self.DownloadPath + self.search + "/" + self.year + "/texts/") 
            except:
                pass
            try:
                os.mkdir(self.DownloadPath + self.search + "/" + self.year + "/texts/brazilian/") 
            except:
                pass
            try:
                os.mkdir(self.DownloadPath + self.search + "/" + self.year + "/texts/english/") 
            except:
                pass
                

        def runBrazil(self):
            self.grabLinks()
            self.savePdf()
            self.pdfToText()
            self.toEnglish()

        def grabLinks(self):
            try:

                # Get the list of pages and find the last page
                for link in self.soup.find_all('a'):
                    print link.get('onclick')
                    if link.get('onclick') != None:
                        self.ultimo = link.get('onclick')
                print self.ultimo
                self.ultimo = re.findall(r'\d+', str(self.ultimo))
                print self.ultimo


                # Go through the pages, putting all of the links into a list
                for i in range(int(self.ultimo[0])):
                    print ("on page " + str(i+1) + " out of " + str(self.ultimo))

                    # Set the POST data list
                    self.dataList = {'edicao.paginaAtual':i,'edicao.fonetica':'null','edicao.txtPesquisa':self.search,'edicao.dtInicio':self.startDate,'edicao.dtFim':self.endDate,'edicao.ano':self.year}
                    
                    # Go to the specified numbered page
                    while True:
                        try:
                            self.rPost = requests.post("http://pesquisa.in.gov.br/imprensa/core/consulta.action", data=self.dataList)
                            self.soup = BeautifulSoup(self.rPost.content, 'html.parser')
                            if "Proxy Error" in self.rPost.content or len(self.soup.find_all('a')) < 2:
                                print "Proxy Error or nothing there"
                                self.r.Post = requests.post("http://pesquisa.in.gov.br/imprensa/core/consulta.action", data=self.dataList)
                                self.soup = BeautifulSoup(self.rPost.content, 'html.parser')
                            else:
                                break
                        except:
                            print "In except. Retry."
                            

                    # Get all the links on the page and append it to a list. 
                    for link in self.soup.find_all('a'):
                        if "pesquisa" in link.get('href'):
                            theLink = link.get('href').replace("jsp/visualiza/index.jsp","servlet/INPDFViewer") + "&captchafield=firistAccess"
                            self.linkList.append(theLink)
                            # Add the links to the tsv file immediately for safe keeping
                            try:
                                fd = open(self.DownloadPath + self.search + "/" + self.year + "/" + self.search + self.year + ".tsv",'ab')
                                fd.write(theLink)
                                fd.close()
                            except:
                                fd = open(self.DownloadPath + self.search + "/" + self.year + "/" + self.search + self.year + ".tsv",'wb')
                                fd.write(theLink)
                                fd.close()


                num_links = len(self.linkList)
                print ("num_links is " + str(num_links))

                # Finally, readd everything to the tsv file
                df = pd.DataFrame(self.linkList)
                df.to_csv(self.DownloadPath + self.search + "/" + self.year + "/" + self.search + self.year + ".tsv", index=False, header="Links")
            except Exception, e:
                #e = sys.exc_info()[0]
                content = repr(e)
                #content = traceback.format_exc()
                mail = smtplib.SMTP('smtp.gmail.com',587)
                mail.ehlo()
                mail.starttls()
                mail.login('westerfeldfan@gmail.com','Rheticus@Me9')
                mail.sendmail('westerfeldfan@gmail.com','bljackson@email.wm.edu', content)
                mail.close()
                print("Sent")
                df = pd.DataFrame(self.linkList)
                df.to_csv(self.DownloadPath + self.search + "/" + self.year + "/" + self.search + self.year + ".tsv", index=False, header="Links")
                #self.logger.exception('Unhandled Exception')
                print "Unexpected error:", sys.exc_info()[0]
                raise
                

        def savePdf(self):
            try:
                num_links = len(self.linkList)
                print ("num_links is " + str(num_links))

                #print ("Number of links " + str(num_links))

                # For each link in the list of links
                for i in range(num_links):

                    print i
                    # Denote which link is the current link based on i
                    self.current_link = self.linkList[i]

                    # Change the filename to a better file name. So split it so it's just the end of the url
                    temp, filename = self.current_link.split('?')
                    # Then replace the /'s with -'s for betterness.
                    filename = filename.replace('/','-')
                    print self.current_link

                    print filename
                    #time.sleep(0.1)

                    # Open the pdf file online and it saves it automatically. 
                    while True:
                        try:
                            urllib.urlretrieve(self.current_link, (self.DownloadPath + self.search + "/" + self.year + '/pdfs/' + filename + ".pdf"))
                            break
                        except:
                            print "Retry grabbing pdf"
                    #urllib.urlretrieve(self.current_link, (self.DownloadPath + self.search + "/" + self.year + '/pdfs/' + filename + ".pdf"))
                            
                    #print os.listdir(self.DownloadPath + self.search + "/pdfs/")
                    print
                    print "Bottom of loop"

                print "Bottom of savePdfs"
            except Exception, e:
                #e = sys.exc_info()[0]
                content = repr(e)
                mail = smtplib.SMTP('smtp.gmail.com',587)
                mail.ehlo()
                mail.starttls()
                mail.login('westerfeldfan@gmail.com','Rheticus@Me9')
                mail.sendmail('westerfeldfan@gmail.com','bljackson@email.wm.edu', content)
                mail.close()
                print("Sent")
                #self.logger.exception('Unhandled Exception')
                print "Unexpected error:", sys.exc_info()[0]
                raise


        def pdfToText(self):
            try:
                print "inside pdfToText"
                for pdf in os.listdir(self.DownloadPath + self.search + "/" + self.year + '/pdfs/'):
                    #print ("pdf is " + str(pdf))

                    if (pdf[:-4] + ".txt") not in os.listdir(self.DownloadPath + self.search + "/" + self.year + '/texts/brazilian/'):
                        fp = open(self.DownloadPath + self.search + "/" + self.year + '/pdfs/' + pdf, 'rb')
                        rsrcmgr = PDFResourceManager()
                        retstr = StringIO()
                        codec = 'utf-8'
                        laparams = LAParams()
                        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
                        # Create a PDF interpreter object.
                        interpreter = PDFPageInterpreter(rsrcmgr, device)
                        # Process each page contained in the document.

                        for page in PDFPage.get_pages(fp):
                            interpreter.process_page(page)
                            data =  retstr.getvalue()

                        data = data.encode('utf-8')
                        #print data

                        file = codecs.open(self.DownloadPath + self.search + "/" + self.year + "/texts/brazilian/" + (pdf[:-4] + ".txt"), "wb", "utf-8")
                        file.write(data)
                        file.close()
            except Exception, e:
                #e = sys.exc_info()[0]
                content = repr(e)
                mail = smtplib.SMTP('smtp.gmail.com',587)
                mail.ehlo()
                mail.starttls()
                mail.login('westerfeldfan@gmail.com','Rheticus@Me9')
                mail.sendmail('westerfeldfan@gmail.com','bljackson@email.wm.edu', content)
                mail.close()
                print("Sent")
                #self.logger.exception('Unhandled Exception')
                print "Unexpected error:", sys.exc_info()[0]
                raise
 
        def toEnglish(self):
            try:
                gs = goslate.Goslate()
                for text in os.listdir(self.DownloadPath + self.search + "/" + self.year + '/texts/brazilian/'):
                    print ("Translating file " + text)
                    if (text[:-4] + "english.txt") not in os.listdir(self.DownloadPath + self.search + "/" + self.year + '/texts/english/'):
                        fp = open(self.DownloadPath + self.search + "/" + self.year + '/texts/brazilian/' + text)
                        fileText = fp.read()
                        translated = gs.translate(fileText,'en')
                        file = codecs.open(self.DownloadPath + self.search + "/" + self.year + '/texts/english/' + (text[:-4] + "english.txt"), "wb", "utf-8")
                        file.write(translated)
                        file.close()
            except Exception, e:
                content = repr(e)
                mail = smtplib.SMTP('smtp.gmail.com',587)
                mail.ehlo()
                mail.starttls()
                mail.login('westerfeldfan@gmail.com','Rheticus@Me9')
                mail.sendmail('westerfeldfan@gmail.com','bljackson@email.wm.edu', content)
                mail.close()
                print("Sent")
                #self.logger.exception('Unhandled Exception')
                print "Unexpected error:", sys.exc_info()[0]
                raise

except Exception, e:
    #e = sys.exc_info()[0]
    content = repr(e)
    mail = smtplib.SMTP('smtp.gmail.com',587)
    mail.ehlo()
    mail.starttls()
    mail.login('westerfeldfan@gmail.com','Rheticus@Me9')
    mail.sendmail('westerfeldfan@gmail.com','bljackson@email.wm.edu', content)
    mail.close()
    print("Sent")
    #self.logger.exception('Unhandled Exception')
    print "Unexpected error:", sys.exc_info()[0]
    raise

if __name__ == "__main__":
    input = raw_input
    search = (input('search Query: ')).rstrip('\r\n').strip()
    print 
    startDate = (input('Start Date (dd/mm): ')).rstrip('\r\n').strip()
    print
    endDate = (input('End Date (dd/mm): ')).rstrip('\r\n').strip()
    print
    year = (input('Year: ')).rstrip('\r\n').strip()
    print

    brazil = Brazil(search,startDate,endDate,year)
    brazil.runBrazil()

    # Email
    content = 'Finished'
    mail = smtplib.SMTP('smtp.gmail.com',587)
    mail.ehlo()
    mail.starttls()
    mail.login('westerfeldfan@gmail.com','Rheticus@Me9')
    mail.sendmail('westerfeldfan@gmail.com','bljackson@email.wm.edu', content)
    mail.close()
    print("Sent")
