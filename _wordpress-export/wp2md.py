#!/usr/bin/env python
#######################################################
# File: wp2sc.py                                      #
# Date: 31 January 2011                               #
# Auth: Jeremy A. Gibbs                               #
# Depn: Requires BeautifulSoup and html2text          #
# Desc: This script reads in a Wordpress .xml export  #
#       file and converts the contents into markdown  #
#       formatted files suitable to import into       #
#       Marco Arment's Second Crack static blogging   #
#       engine.                                       #
# Orig: https://gist.github.com/1239373 (by Reiot)    #
#       Original was for wordpress to octopress       #
# Fork: https://gist.github.com/1709782               #
#       I rewrote/cleaned up script to read my own    #
#       WordPress structure and to output in the      #
#       specific format Second Crack requires         #
#######################################################
import os, sys, urllib, codecs
from datetime import datetime
from bs4 import BeautifulSoup
import html2text

#################
# Configuration #
#################
wpXML      = "rowant.wordpress.2014-12-29.xml"
format     = '%04d-%02d-%02d-%s.txt'
statFilter = [u'publish']
postFilter = [u'post', u'page']
metaFilter = [u'Link']
ctgyFilter = [u'Uncategorized']
tagsFilter = []
writeCats  = False
writeTags  = True
writeExtra = False

##############
# XML Parser #
##############
def parse_item(item):

    # return unicode of a selection
    def _(node):
        if not node or not node.string:
            return u''            
        u = unicode(node.string)
        if u.startswith(u'<![CDATA['):
            u = u[9:-3]
        return u
    
    # only grab posts and pages
    postType = _(item.find("wp:post_type")) 
    if postType not in postFilter:
        return
    
    # only grab published articles
    wp_status = _(item.find("wp:status")) 
    if wp_status not in statFilter:
        return
        
    # article title
    title = _(item.find("title"))
    tLen  = len(title)
    
    # article publication date
    postDate = _(item.find("wp:post_date")) 
    postDate = datetime.strptime(postDate,"%Y-%m-%d %H:%M:%S")

    # article slug name
    slug = _(item.find("wp:post_name"))
    slug = urllib.unquote(slug.encode('utf-8')).decode('utf-8')
    assert isinstance(slug, unicode), 'slug should be unicode'
        
    # markdown output file
    outFile = u'%04d-%02d-%02d-%s.markdown'%(postDate.year, postDate.month, postDate.day, slug)
    outPath = os.path.join(u"source", u"_%ss"% postType)
    if not os.access( outPath, os.F_OK ):
        os.mkdir( outPath )
    out = codecs.open( os.path.join(outPath, outFile), "w",  encoding='utf-8')
    
    # write title and separator
    out.write(u'---\n')
    out.write(u'layout: post\n')
    out.write(u'title: "%s"\n'%title)
        
    # check for linked post (if stored as meta value)
    has_meta = {}
    for meta in item.findAll("wp:postmeta"):
        key   = _(meta.find("wp:meta_key"))
        value = _(meta.find("wp:meta_value"))
        if key in metaFilter:
            has_meta[key] = value
    if has_meta:
        for key, value in has_meta.iteritems():
            out.write(u'%s: %s\n'%(key, value))
            out.write(u'Type: link\n')
    
    # publication date
    out.write(u'date: %s\n'% postDate)
    out.write(u'---\n')

    
    # categories
    if (writeCats):
        categories = []
        for category in item.findAll("category",{"domain":"category"}):
            categories.append(_(category))
        categories = list(set([c for c in categories if c not in ctgyFilter]))
        if categories:
            out.write(u'Categories:')
            for category in categories:
                out.write(u' %s,'% category)
            out.write(u'\n')
    
    # tags
    if (writeTags):
        tags = []
        for tag in item.findAll("category",{"domain":"tag"}):
            tags.append(_(tag))
        tags = list(set([t for t in tags if t not in tagsFilter]))
        if tags:
            out.write(u'Tags:')
            for tag in tags:
                out.write(u' %s,'% tag)
            out.write(u'\n')

    # extras
    if (writeExtra):
        # comment status
        wp_comment_status = _(item.find("wp:comment_status")) 
        out.write(u'comments: %s\n'% ('true' if wp_comment_status == u'open' else 'false'))
                
        # old permlink
        link = _(item.find("link"))
        out.write(u'link: %s\n'% link)
    
    # article body in markdown format
    body = _(item.find("content:encoded"))
    body = body.strip()
    body = body.replace('\n', '</p><p>')
    body = '<p>' + body

    h = html2text.HTML2Text()
    h.body_width = 0
    body = h.handle(body)

    out.write(body)
    out.close()    
        
if __name__ == '__main__':

    print 'Reading WordPress XML Export File'
    xml = BeautifulSoup(open(wpXML))
    print 'Parsing WordPress XML Export File'
    for item in xml.findAll("item"):
        parse_item(item)
    print 'Conversion Completed'