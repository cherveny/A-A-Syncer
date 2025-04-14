# -*- coding: utf-8 -*-
"""
Created on Wed Mar  2 15:02:44 2022
Updated Mon 4/12/2025, removing customizations

@author: Bruce Orcutt UTSA Bruce.Orcutt@utsa.edu
"""

# -*- coding: utf-8 -*-


# for requests to ArchiveSpace
import re
import sys
import csv
import json
import requests
import copy
from tkinter import *

# for file dialog specifically
from tkinter.filedialog import  askopenfilename
from tkinter.filedialog import  asksaveasfile

# OS styled buttons, etc to better match user expectations
from tkinter import ttk

# Constants
# your ALMA API key, created via ExLibris Developers site.  
almaKey = ''  
# use your alma instance
almaURL = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/'  
# replace archivespaceURL and API user password
aSpaceLoginURL = "http://ArchivespaceURL:8089/users/apiuser/login?password=XXXX"  
# the numbere here, 3, will change depending on the structure of your repositories
aSpaceBarcodeSearch = "/repositories/3/top_containers/search?q="  
# replace with your URL
aSpaceContentURL = "http://ArchivespaceURL:8089"  
severityLookup = {
    'INFO'      : 'LightBlue',
    'ERROR'     : 'red',
    'SUCCESS'   : 'LimeGreen' 
    }
ALMAheaders = {"Accept": "application/json"}

# to be used to hold a pointer to the CSV file opened by the user
csvFile = ""

predictedFields = ['resource_uri',
 'libname',
 'libcode',
 'locname',
 'loccode']

#Update the URLS to the proper ALMA instace for your instutution
ALMAItemSkeleton = {
  "link": "https://api-na.hosted.exlibrisgroup.com/almaws/v1/bibs/{{mms_id}}",
  "holding_data": {
    "link": "https://api-na.hosted.exlibrisgroup.com/almaws/v1/bibs/{{mms_id}}/holdings/{{holding_id}}",
    "holding_id": "{{holding_id}}",
    "copy_id": "1",
    "in_temp_location": "false",
    "due_back_date": "2015-07-20"
  },
  "item_data": {
    "barcode": "{{Barcode}}",
    "physical_material_type": {
      "value": "BOX",
      "desc": "BOX"
    },
    "policy": {
      "value": "",
      "desc": ""
    },
    "provenance": {
      "value": "",
      "desc": "null"
    },
    "po_line": "",
    "is_magnetic": "false",
    "arrival_date": "2020-02-14Z",
    "year_of_issue": "",
    "enumeration_a": "{{description}}",
    "enumeration_b": "",
    "enumeration_c": "",
    "enumeration_d": "",
    "enumeration_e": "",
    "enumeration_f": "",
    "enumeration_g": "",
    "enumeration_h": "",
    "chronology_i": "",
    "chronology_j": "",
    "chronology_k": "",
    "chronology_l": "",
    "chronology_m": "",
    "description": "{{description}}",
    "receiving_operator": "import",
    "process_type": {
      "value": "",
      "desc": "null"
    },
    "inventory_number": "",
    "inventory_price": "",
    "library": {
      "value": "{{libcode}}",
      "desc": "{{libname}}"
    },
    "location": {
     "value": "{{loccode}}",
      "desc": "{{locname}}"
    },
    "alternative_call_number": "{{description}}",
    "alternative_call_number_type": {
      "value": "8",
      "desc": "OTHER"
    },
    "storage_location_id": "",
    "pages": "",
    "pieces": "",
    "public_note": "",
    "fulfillment_note": "",
    "internal_note_1": "",
    "internal_note_2": "",
    "internal_note_3": "",
    "statistics_note_1": "",
    "statistics_note_2": "",
    "statistics_note_3": "",
    "requested": "false",
    "edition": "null",
    "imprint": "null",
    "language": "null",
  }
}


root = Tk()
mess = Tk()
mess.minsize(350,600)

message_list = []

  
def add_message(messageText,severity):
    ListB.insert(END, messageText)
    ListB.itemconfig(ListB.size()-1,bg=severityLookup[severity])

def process_csv():
    # main processing function
    row_count = 0
    
    try:
        filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file    
    except Exception as e:
        add_message("ERROR, was unable to select CSV file to open. Error: "+str(e), "ERROR")
    
    
    with open(filename) as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
    
        # ensure proper field headers to verify proper file format
        if csv_reader.fieldnames != predictedFields :
            add_message("ERROR.  Bad file format! CSV Headers have changed! I see: "+str(csv_reader.fieldnames), "ERROR")
            return
        
        add_message("Starting Processing Items","SUCCESS")
        for row in csv_reader:
            # start of loop init
            barcode     = "x"
            resourceURI = ""
            libname     = ""
            libcode     = ""
            locname     = ""
            loccode     = ""
            response    = ""
            
            row_count += 1
            
            # load row variables
            resourceURI = row["resource_uri"]
            libname     = row["libname"]
            libcode     = row["libcode"]
            locname     = row["locname"]
            loccode     = row["loccode"]
            
           
            # start getting values we need
            mmsID = getAspaceMMS(resourceURI)
            holdingID = getALMAHoldingId(mmsID)
            topContainers = getAspaceContainers(resourceURI)
           
            # topContainers is a dict with ALL the top containers.  Need to loop over them
            # length, given a dict, is number of items contained.
            for count  in range(0, len(topContainers) -1,1):
               barcode = str(getAspaceBarcode(topContainers[count]['ref']))
               
               #print("barcode is "+barcode)
               addALMAItem(barcode, mmsID, holdingID,libname,libcode,locname,loccode)
               mess.update()
                
            add_message("Final item from current row complete", "SUCCESS")
        add_message("ALL ITEMS COMPLETE", "SUCCESS")
        
        
    
        
def close_all():
    # cleanup function
    root.destroy()
    mess.destroy()

def setup_window():
    # start TK
    global root 
    global mess    
    global ListB 
    global scroll

    # TITLES
    label = ttk.Label(root,text="ASpace/ALMA Item Sync",font="Helvetica 18 bold")
    label.pack()

    label = ttk.Label(mess,text="Transaction Message Log", font="Helvetica 18 bold")
    label.pack()



    # Logs into ASpace, gets an authorizaiton key.
    loadButton = ttk.Button(root,text="Login to ASpace")
    loadButton.pack()
    loadButton['command'] = aSpaceLogin
    
    # starts the actual loading process
    loadButton = ttk.Button(root,text="Load and Process CSV File")
    loadButton.pack()
    loadButton['command'] = process_csv

    # set up the exit button        
    exitButton = ttk.Button(root,text="Exit")
    exitButton.pack()
    exitButton['command'] = close_all
    
    #set up log window
    scroll = Scrollbar(mess, orient="vertical")     
    ListB = Listbox(mess,yscrollcommand=scroll.set,relief=RIDGE,borderwidth=4)
    ListB.pack(side=LEFT,fill=BOTH,expand=True)
    scroll.pack(side=RIGHT)
    scroll.config(command=ListB.yview)
   

def aSpaceLogin():
    global sessionKey
    global aSpaceHeaders
    
    response = ""
    
    # log in to aspace, get session key
    try:
        response =  requests.post(aSpaceLoginURL)
        incJSON = response.json()
        sessionKey = incJSON["session"]
        aSpaceHeaders = {"X-ArchivesSpace-Session": sessionKey}
    except:  
        add_message("Error logging in to ASpace. (EXCEPTION) Please try again","ERROR")
        return
    
    if (response.status_code == 200):
        add_message("Logged into ASpace", "SUCCESS")
    else: 
        add_message("Error logging into ASpace("+response.status_code+"): Please try again")
        
def getAspaceMMS(resourceURI):
     global sessionKey
     global aSpaceHeaders
     # Get the MMS ID from ASpace to use as a key into ALMA (bib id)
     
     mmsID = 0
     response = requests.get(aSpaceContentURL+resourceURI,headers=aSpaceHeaders)
     incJSON = response.json()
     mmsID = incJSON["user_defined"]["string_2"]
     
     return(mmsID)

def getALMAHoldingId(mmsID):
    # given an bib, find the associated holdint ID
    global almaKey
    global almaURL
    global ALMAheaders
    
    holdingID = 0
    
    URL = almaURL+"bibs/"+mmsID+"/holdings?apikey="+almaKey
    response = requests.get(URL,headers=ALMAheaders)
    incJSON = response.json()
    holdingID = incJSON["holding"][0]["holding_id"]
    return(holdingID)

def getAspaceContainers(resourceURI):
    # get all containers in a URI
    
    topContainers = ""
    URL = aSpaceContentURL + resourceURI + "/top_containers"
    response = requests.get(URL,headers=aSpaceHeaders)
    incJSON = response.json()
    topContainers = incJSON
    return(topContainers)

def getAspaceBarcode(resourceURI):
    # get the barcode for the current aspace item
    barcode = ""
    URL = aSpaceContentURL + resourceURI
    response = requests.get(URL,headers=aSpaceHeaders)
    incJSON = response.json()
    barcode = incJSON['barcode']
    return(barcode)

def addALMAItem(barcode,mmsID,holdingID,libname,libcode,locname,loccode):
    # add the found item from ASpace into ALMA
    almaItem = copy.deepcopy(ALMAItemSkeleton)
    URL = aSpaceContentURL + aSpaceBarcodeSearch + barcode
    response = requests.get(URL,headers=aSpaceHeaders)
    incJSON = response.json()
    
    # Description field, lists exact box name/place usually
    shelf = incJSON["response"]["docs"][0]["title"]  
    
    # modify our skeleton, filling in the blanks with our info from the previous queries
    almaItem["link"] = almaItem["link"].replace("{{mms_id}}",mmsID)
    almaItem["holding_data"]["link"] = almaItem["holding_data"]["link"].replace("{{mms_id}}",mmsID)
    almaItem["holding_data"]["link"] = almaItem["holding_data"]["link"].replace("{{holding_id}}",holdingID) 
    almaItem["item_data"]["barcode"] = almaItem["item_data"]["barcode"].replace("{{Barcode}}",barcode)
    almaItem["item_data"]["description"] = almaItem["item_data"]["description"].replace("{{description}}",shelf)
    almaItem["item_data"]["enumeration_a"] = almaItem["item_data"]["enumeration_a"].replace("{{description}}",shelf)
    almaItem["item_data"]["alternative_call_number"] = almaItem["item_data"]["alternative_call_number"].replace("{{description}}",shelf)
    almaItem["item_data"]["library"]["desc"]  = almaItem["item_data"]["library"]["desc"].replace("{{libname}}",libname)
    almaItem["item_data"]["library"]["value"]  = almaItem["item_data"]["library"]["value"].replace("{{libcode}}",libcode)
    almaItem["item_data"]["location"]["desc"]  = almaItem["item_data"]["location"]["desc"].replace("{{locname}}",locname)
    almaItem["item_data"]["location"]["value"]  = almaItem["item_data"]["location"]["value"].replace("{{loccode}}",loccode)
    
    URL = almaURL+"bibs/"+mmsID+"/holdings/"+holdingID+"/items?apikey="+almaKey
    
    response = requests.post(URL,headers=ALMAheaders,json=almaItem)
    incJSON = response.json()
          
    if(response.status_code ==  400):
        # cpde 400, item exists
        add_message("Item " + barcode + " already exists, not adding", "INFO")
        #print(str(incJSON))
    elif (response.status_code == 200):
        # Code 200, success
        add_message("New Item " + barcode + "adding", "SUCCESS")
    else:
        # all other cases, error
        add_message("Item ", + barcode + " resulted in error when adding.  (Code="+str(response.status_code)+")","ERROR")
    return (True)


# MAIN TK LOOP
setup_window()
root.mainloop()




