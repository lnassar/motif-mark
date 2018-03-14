#!/usr/bin/python

import re
import cairo
import random
import argparse

parser = argparse.ArgumentParser(description='Given a Fasta file with uppercase exons and a text file with one motif per line, creates an svg image depicting each sequence intronic and exonic region with matching motif regions. NOTE: Uses random color generation, if two motifs share colors that are too similar, please rerun script.')
parser.add_argument('-f', '--fasta', metavar='Fasta File Path', required=True,type=str, help='Absolute file path to Fasta file')
parser.add_argument('-m', '--motif', metavar='Motif File Path', required=True,type=str, help='Absolute file path to motif file')
parser.add_argument('-n', '--name', metavar='Output Image Name', type=str, default=False, help='Optional: Provides the name for the output svg image file')

parser = parser.parse_args()

if parser.name is False: #Add our conditional to check if a custom name was passed
    FileName = "Sequence_Motif"
else:
    FileName = parser.name

#Set our passed variables
InputFile = parser.fasta
InputMotifFile = parser.motif

############################
#Define our functions

#Fixes any ambiguous bases in our motifs for use in your regular expression
def motif_fixer (motif):
    motif = motif.upper()
    motif = motif.replace('Y','[CT]')
    motif = motif.replace('R','[AU]')
    motif = motif.replace('S','[GC]')
    motif = motif.replace('W','[AT]')
    motif = motif.replace('K','[GT]')
    motif = motif.replace('M','[AC]')
    motif = motif.replace('B','[CGT]')
    motif = motif.replace('D','[AGT]')
    motif = motif.replace('H','[ACT]')
    motif = motif.replace('V','[ACG]')
    motif = motif.replace('N','.')
    return motif

#Draws our exons and motifs, depending on start/end sites
def draw_line(x,y,start,stop):
    context.move_to(x+start,y)
    context.line_to(x+stop,y)
    context.stroke()
    
#Draws our legend
def draw_legend(r,g,b,n,motif):
    context.set_source_rgb(r,g,b)
    context.rectangle(n,10,10,10)
    context.fill()
    context.set_source_rgb(0,0,0)
    context.move_to(n + 11,17)
    context.show_text(motif)
    n = n + 10*(len(motif))
    return(n)

#Exonseq looks for the exons by searching for capital letters within the sequence looking for uppercase
#letters that are grouped together, not a function but a compiled reg-expression search
exonseq = re.compile("[A-Z]{1,}")

############################
#If our fasta file is multi-line, we now convert it into a single header + sequence line file

#First we find the total number of lines in the file to account for the final line
total_lines = 0
fh = open(InputFile)
for lines in fh:
    total_lines+=1
fh.close()

#We iterate through our file and join all sequence lines, also makes our file into an iterable list
fh = open(InputFile)
sequence = ""
InputFasta = []
n=0
for lines in fh:
    lines = lines.rstrip()
    n+=1
    if n == 1: #Exception for first line
        InputFasta.append(lines)
        sequence = ""
    elif n == total_lines: #Exception for last line
        sequence = sequence + lines
        InputFasta.append(sequence)
    elif lines.startswith(">"):
        InputFasta.append(sequence)
        InputFasta.append(lines)
        sequence = ""
    elif not lines.startswith(">"):
        sequence = sequence + lines
fh.close()

############################
#Go through both of our input motif and fasta file in order to see how many genes/motifs we'll be looking at in total
#so we can create our plot with sufficient room and colors. Additionally create a list of our fixed motifs(fix ambiguousness)

#Open our fasta file to count the number of genes to find the longest present and account for plot Y axis
entrylength = 0
nlines = 0
for lines in InputFasta:
    if not lines.startswith(">"):
        nlines+=1
        if len(lines) > entrylength:
            entrylength = len(lines)

#Open our motif file and create a list with fixed (no ambiguous bases) motifs
InputMotif = open(InputMotifFile)
motifs = []
for motif in InputMotif:
    motif = motif.rstrip()
    motifs.append(motif_fixer(motif))
InputMotif.close()

#Create three lists pertaining to the colors that will be used to represent each individual motif
red = []
green = []
blue = []
for motif in motifs:
    red.append(random.randint(0,100)/100)
    green.append(random.randint(0,100)/100)
    blue.append(random.randint(0,100)/100)
    
############################
#Create our base x and y draw values and initiate our cairo surface by the calculated values
x = 25 #This can be used to tune how far fromt he margin we wish to start our images/writing
y = 0
surface = cairo.SVGSurface(FileName+".svg", entrylength+(x*2), (nlines*50)+50)
context = cairo.Context(surface)
context.set_font_size(8)

#Draw a legend of what each motif color means
n = 25 #Decides how far down the y acis we wish to start our legend
for motif,r,g,b in zip(motifs,red,green,blue):
    if n == 25:
        n = draw_legend(r,g,b,n,motif)
    else:
        n = draw_legend(r,g,b,n,motif)

############################
#The way we will draw the exons will be to first draw an entire line to signify the whole gene (introns) then for each position in which
#an upper case character was found (exon), we will draw a vertical line. Then we will look at the motifs and draw different
#colored horizontal lines through each respective site

for lines in InputFasta:
    if lines.startswith(">"): #Begin by adding the header above each gene that will be ploted
        y = y + 50
        context.set_source_rgb(0,0,0)
        context.move_to(x,y-15)
        context.show_text(lines)
        
    if not lines.startswith(">"): #Draws our 'intron' line which is simply a line the length of our sequence
        context.set_line_width(1)
        context.move_to(x,y)
        context.line_to(x+len(lines),y)
        context.stroke()
        
        #We set our line width to 10 since we will draw our motifs and exons much wider
        context.set_line_width(10)
        
        #Set and reset our exon start and end variables for each sequence
        exonstart = []
        exonend = []
        
        #Look through our current line and save all the exon start and stop locations
        for bases in exonseq.finditer(lines): #Save the location of every uppercase character in the sequence
            exonstart.append(bases.start()+1) #In order to account for 0 based python counts, we used start + 1
            exonend.append(bases.end())
            
        for start, stop in zip(exonstart,exonend): #Iterate through our start and stop sites to draw our exons
                draw_line(x,y,start,stop)
        
        #Additionall we change our sequence lines to uppercase as the regular expressions are looking for uppercase characters
        lines = lines.upper()
        
        #Iterate through our motif list, as well as the corresponding colors for each motif
        for motif,r,g,b in zip(motifs,red,green,blue):
            #Set and reset our motif stard and end locations for each motif
            motifstart = []
            motifend = []
            motifseq = re.compile(motif,) #Compile our reg-ex search to match for each specific motif
        
            for bases in motifseq.finditer(lines):
                motifstart.append(bases.start()+1) #In order to account for 0 based python counts, we used start + 1
                motifend.append(bases.end())
        
            for start, stop in zip(motifstart,motifend): #Iterate through our start and stop sites to draw our motifs        
                context.set_source_rgb(r,g,b)
                draw_line(x,y,start,stop)


# In[264]:

# #This is the code without the argparse for debugging purposes

# #!/usr/bin/python

# import re
# import cairo
# import random

# InputFile = "sequence.txt"
# InputMotifFile = "motifs2.txt"
# FileName = "FileName"

# ############################
# #Define our functions

# #Fixes any ambiguous bases in our motifs for use in your regular expression
# def motif_fixer (motif):
#     motif = motif.upper()
#     motif = motif.replace('Y','[CT]')
#     motif = motif.replace('R','[AU]')
#     motif = motif.replace('S','[GC]')
#     motif = motif.replace('W','[AT]')
#     motif = motif.replace('K','[GT]')
#     motif = motif.replace('M','[AC]')
#     motif = motif.replace('B','[CGT]')
#     motif = motif.replace('D','[AGT]')
#     motif = motif.replace('H','[ACT]')
#     motif = motif.replace('V','[ACG]')
#     motif = motif.replace('N','.')
#     return motif

# #Draws our exons and motifs, depending on start/end sites
# def draw_line(x,y,start,stop):
#     context.move_to(x+start,y)
#     context.line_to(x+stop,y)
#     context.stroke()
    
# #Draws our legend
# def draw_legend(r,g,b,n,motif):
#     context.set_source_rgb(r,g,b)
#     context.rectangle(n,10,10,10)
#     context.fill()
#     context.set_source_rgb(0,0,0)
#     context.move_to(n + 11,17)
#     context.show_text(motif)
#     n = n + 10*(len(motif))
#     return(n)

# ############################
# #If our fasta file is multi-line, we now convert it into a single header + sequence line file

# #First we find the total number of lines in the file to account for the final line
# total_lines = 0
# fh = open(InputFile)
# for lines in fh:
#     total_lines+=1
# fh.close()

# #We iterate through our file and join all sequence lines, also makes our file into an iterable list
# fh = open(InputFile)
# sequence = ""
# InputFasta = []
# n=0
# for lines in fh:
#     lines = lines.rstrip()
#     n+=1
#     if n == 1: #Exception for first line
#         InputFasta.append(lines)
#         sequence = ""
#     elif n == total_lines: #Exception for last line
#         sequence = sequence + lines
#         InputFasta.append(sequence)
#     elif lines.startswith(">"):
#         InputFasta.append(sequence)
#         InputFasta.append(lines)
#         sequence = ""
#     elif not lines.startswith(">"):
#         sequence = sequence + lines
# fh.close()

# ############################
# #Go through both of our input motif and fasta file in order to see how many genes/motifs we'll be looking at in total
# #so we can create our plot with sufficient room and colors. Additionally create a list of our fixed motifs

# #Open our fasta file to count the number of genes to find the longest present and account for plot Y axis
# entrylength = 0
# nlines = 0
# for lines in InputFasta:
#     if not lines.startswith(">"):
#         nlines+=1
#         if len(lines) > entrylength:
#             entrylength = len(lines)

# #Open our motif file and create a list with fixed (no ambiguous bases) motifs
# InputMotif = open(InputMotifFile)
# motifs = []
# for motif in InputMotif:
#     motif = motif.rstrip()
#     motifs.append(motif_fixer(motif))
# InputMotif.close()

# #Create three lists pertaining to the colors that will be used to represent each individual motif
# red = []
# green = []
# blue = []
# for motif in motifs:
#     red.append(random.randint(0,100)/100)
#     green.append(random.randint(0,100)/100)
#     blue.append(random.randint(0,100)/100)
    
# ############################
# #Create our base x and y draw values and initiate our cairo surface by the calculated values
# x = 25
# y = 0
# surface = cairo.SVGSurface(FileName+".svg", entrylength+(x*2), (nlines*50)+50)
# context = cairo.Context(surface)
# context.set_font_size(8)

# #Exonseq looks for the exons by searching for capital letters within the sequence
# exonseq = re.compile("[A-Z]")

# #Draw a legend of what each motif color means
# n = 25
# for motif,r,g,b in zip(motifs,red,green,blue):
#     if n == 25:
#         n = draw_legend(r,g,b,n,motif)
#     else:
#         n = draw_legend(r,g,b,n,motif)

# ############################
# #The way we will draw the exons will be to first draw an entire line to signify the whole gene (introns) then for each position in which
# #an upper case character was found (exon), we will draw a vertical line. Then we will look at the motifs and draw different
# #colored horizontal lines through each respective site


# for lines in InputFasta:
#     if lines.startswith(">"): #Begin by adding the header above each gene that will be ploted
#         y = y + 50
#         context.set_source_rgb(0,0,0)
#         context.move_to(x,y-15)
#         context.show_text(lines)
        
#     if not lines.startswith(">"): #Start by drawing our 'intron' line which is simply a line the length of our sequence
#         context.set_line_width(1)
#         context.move_to(x,y)
#         context.line_to(x+len(lines),y)
#         context.stroke()
        
#         #We set our line width to 10 since we will draw our motifs and exons to look pronounced
#         context.set_line_width(10)
        
#         #Compite our regular expression search that looks for uppercase letters that are grouped together
#         exonseq = re.compile("[A-Z]{1,}")
#         exonstart = []
#         exonend = []
        
#         #Look through our current line and save all the exon start and stop locations
#         for bases in exonseq.finditer(lines): #Save the location of every uppercase character in the sequence
#             exonstart.append(bases.start()+1) #In order to account for 0 based python counts, we used start + 1
#             exonend.append(bases.end())
            
#         for start, stop in zip(exonstart,exonend): #Iterate through our start and stop sites to draw our exons
#                 draw_line(x,y,start,stop)
        
#         #Additionall we change our sequence lines to uppercase as the regular expressions are looking for uppercase characters
#         lines = lines.upper()
        
#         #Iterate through our motif list, as well as the corresponding colors for each motif
#         for motif,r,g,b in zip(motifs,red,green,blue):
#             motifstart = [] #to be moved
#             motifend = [] #to be moved
#             motifseq = re.compile(motif,)
        
#             for bases in motifseq.finditer(lines):
#                 motifstart.append(bases.start()+1) #In order to account for 0 based python counts, we used start + 1
#                 motifend.append(bases.end())
        
#             for start, stop in zip(motifstart,motifend): #Iterate through our start and stop sites to draw our motifs        
#                 context.set_source_rgb(r,g,b)
#                 draw_line(x,y,start,stop)

