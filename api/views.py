from django.http.response import JsonResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

import os
import json

import firebase_admin
from firebase_admin import credentials, auth, firestore, messaging
from firebase_admin.firestore import SERVER_TIMESTAMP

if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.join( settings.BASE_DIR, 'static/key.json' ))
    firebase_admin.initialize_app(cred)

firestore_db = firestore.client()


EOD_API_KEY = "61d5da6b638f50.66949714";

STOCK_DATA_API = "https://eodhistoricaldata.com/api/real-time/NETF.NSE?api_token={}&fmt=json".format(EOD_API_KEY);

############################################
################## AUTH ####################
############################################

@api_view(['POST'])
def register_user(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']
            name = request.POST['name']
            phoneNum = request.POST['phoneNum']
            gender = request.POST['gender']
            risk = request.POST['risk']
            timeframe = request.POST['timeframe']

            firestore_db.collection(u'users').document(u'customers').collection(u'users').document(uid).set({
                'name': name,
                'phoneNum': phoneNum,
                'gender': gender,
                'risk': risk,
                'timeframe': timeframe,
                'createdAt': SERVER_TIMESTAMP,
            })

            return Response(data={"result" : "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def check_user(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']

            user = firestore_db.collection(u'users').document(u'customers').collection(u'users').document(uid).get()

            if user.exists:
                return Response(data={"result": "success", "isNew": False, "isAdmin": False}, status=200)
            else:
                isAdmin = firestore_db.collection(u'users').document(u'admin').collection(u'users').document(uid).get().exists

                if isAdmin:
                    return Response(data={"result": "success", "isNew": False, "isAdmin": True}, status=200)
                else:
                    return Response(data={"result": "success", "isNew": True, "isAdmin": False}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def register_admin(request):
    if request.method == "POST":
        try:
            name = request.POST['name']
            email = request.POST['email']
            phoneNum = request.POST['phoneNum']
            password = request.POST['password']


            existingUserID = ""
            try:
                user = auth.get_user_by_phone_number(phoneNum)
                existingUserID = user.uid
            except:
                pass

            if existingUserID != "":
                existingUserID = user.uid

                auth.update_user(
                    existingUserID,
                    email=email,
                    password=password,
                    display_name=name,
                )

                firestore_db.collection(u'users').document(u'admin').collection(u'users').document(existingUserID).update({
                    "name": name,
                    "email": email,
                    "phoneNum": phoneNum,
                })

                return Response(data={"result": "success"}, status=200)
            else:
                newUser = auth.create_user(
                    email=email,
                    password=password,
                    display_name=name,
                    phone_number=phoneNum
                )

                firestore_db.collection(u'users').document(u'admin').collection(u'users').document(newUser.uid).set({
                    "name": name,
                    "email": email,
                    "phoneNum": phoneNum,
                })

                return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

############################################
################ CUSTOMER ##################
############################################

@api_view(['POST'])
def get_recommended_stocks(request):
    if request.method == "POST":
        try:
            phoneNum = request.POST['phoneNum']

            recommendedStocks = firestore_db.collection(u'recommended').where(u'users', "array_contains", phoneNum).get()

            recommendedStocksList = []

            for stock in recommendedStocks:
                stockObj = stock.to_dict()
                stockObj['id'] = stock.id
                stockID = stockObj['stockID']
                
                stockDetails = (firestore_db.collection(u'stocks').document(stockID).get()).to_dict()
                stockDetails['open'] = 180.1
                stockDetails['high'] = 185
                stockDetails['low'] = 178.5
                stockDetails['close'] = 184.74
                stockDetails['volume'] = 4032
                stockDetails['change'] = 3.11
                stockDetails['change_p'] = 1.7123

                stockObj['stock'] = stockDetails
                
                recommendedStocksList.append(stockObj)

            return Response(data={"result": "success", "stocks": recommendedStocksList}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def place_order(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']
            phoneNum = request.POST['phoneNum']
            stockID = request.POST['stockID']

            possibleAdmins = []
            possibleAdminTokens = []

            admins = firestore_db.collection(u'users').document(u'admin').collection(u'users').get()
            userContacts = firestore_db.collection(u'users').document(u'customers').collection(u'users').document(uid).collection(u'contacts').get()

            allAdmins = {}
            allAdminsTokens = {}

            for admin in admins:
                adminId = admin.id
                adminContacts = firestore_db.collection(u'users').document(u'admin').collection(u'users').document(adminId).collection(u'contacts').get()

                adminObj = admin.to_dict()

                for contact in adminContacts:
                    contactObj = contact.to_dict()

                    if contactObj['phoneNum'] == phoneNum:
                        possibleAdmins.append(adminObj['phoneNum']) 
                        if 'token' in adminObj:
                            possibleAdminTokens.append(adminObj['token'])

                allAdmins[adminId] = adminObj['phoneNum']
                if 'token' in adminObj:
                    allAdminsTokens[adminId] = adminObj['token']

            userContactsList = []
            for contact in userContacts:
                contactObj = contact.to_dict()
                userContactsList.append(contactObj['phoneNum'])

            for adminId in allAdmins.keys():
                adminPhoneNum = allAdmins[adminId]
                adminToken = allAdminsTokens[adminId]
                if adminPhoneNum in userContactsList:
                    possibleAdmins.append(adminPhoneNum)
                    possibleAdminTokens.append(adminToken)

            firestore_db.collection(u'orders').document().set({
                'admins': possibleAdmins,
                'amount': float(json.loads(request.POST['amount'])),
                'buyPrice': float(json.loads(request.POST['buyPrice'])),
                'customerID': uid,
                'quantity': float(json.loads(request.POST['quantity'])),
                'stockID': stockID,
                'status': "Ordered",
                "createdAt": SERVER_TIMESTAMP,
            })

            firestore_db.collection(u'users').document(u'customers').collection(u'users').document(uid).collection(u'portfolio').document().set({
                'admins': possibleAdmins,
                'amount': float(json.loads(request.POST['amount'])),
                'buyPrice': float(json.loads(request.POST['buyPrice'])),
                'customerID': uid,
                'quantity': float(json.loads(request.POST['quantity'])),
                'stockID': stockID,
                'status': "Ordered",
                "createdAt": SERVER_TIMESTAMP,
            })

            userName = (auth.get_user(uid=uid)).display_name

            stockName = (firestore_db.collection(u'stocks').document(stockID).get()).to_dict()['name']

            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title="New Order!",
                    body="{} placed an order for {}".format(userName, stockName)
                ),
                tokens=possibleAdminTokens,
            )
            messaging.send_multicast(message)

            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def get_portfolio(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']

            portfolio = firestore_db.collection(u'users').document(u'customers').collection(u'users').document(uid).collection(u'portfolio').get()

            portfolioList = []

            for stock in portfolio:
                stockObj = stock.to_dict()
                stockObj['id'] = stock.id

                stockID = stockObj['stockID']
                stockDetails = (firestore_db.collection(u'stocks').document(stockID).get()).to_dict()
                stockDetails['open'] = 180.1
                stockDetails['high'] = 185
                stockDetails['low'] = 178.5
                stockDetails['close'] = 184.74
                stockDetails['volume'] = 4032
                stockDetails['change'] = 3.11
                stockDetails['change_p'] = 1.7123

                stockObj['stock'] = stockDetails

                portfolioList.append(stockObj)

            return Response(data={"result": "success", "portfolio": portfolioList}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def get_customer_orders(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']

            orders = firestore_db.collection(u'orders').where('customerID', "==", uid).get()

            ordersList = []

            for order in orders:
                orderObj = order.to_dict()
                orderObj['id'] = order.id

                stockID = orderObj['stockID']
                stockDetails = (firestore_db.collection(u'stocks').document(stockID).get()).to_dict()
                stockDetails['open'] = 180.1
                stockDetails['high'] = 185
                stockDetails['low'] = 178.5
                stockDetails['close'] = 184.74
                stockDetails['volume'] = 4032
                stockDetails['change'] = 3.11
                stockDetails['change_p'] = 1.7123

                orderObj['stock'] = stockDetails

                ordersList.append(orderObj)

            return Response(data={"result": "success", "orders": ordersList}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def add_to_portfolio(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']
            stockID = request.POST['stockID']
            
            firestore_db.collection(u'users').document(u'customers').collection(u'users').document(uid).collection(u'portfolio').document().set({
                'stockID': stockID,
            })

            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

############################################
################## Admin ###################
############################################

@api_view(['POST'])
def get_admin_recommendations(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']

            recommendedStocks = firestore_db.collection(u'recommended').where(u'createdBy', "==", uid).get()

            recommendedStocksList = []

            for stock in recommendedStocks:
                stockObj = stock.to_dict()
                stockObj['id'] = stock.id
                stockID = stockObj['stockID']
                
                stockDetails = (firestore_db.collection(u'stocks').document(stockID).get()).to_dict()
                stockDetails['open'] = 180.1
                stockDetails['high'] = 185
                stockDetails['low'] = 178.5
                stockDetails['close'] = 184.74
                stockDetails['volume'] = 4032
                stockDetails['change'] = 3.11
                stockDetails['change_p'] = 1.7123

                stockObj['stock'] = stockDetails
                
                recommendedStocksList.append(stockObj)

            return Response(data={"result": "success", "stocks": recommendedStocksList}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def make_recommendation(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']
            phoneNum = request.POST['phoneNum']

            recommendation = json.loads(request.POST['recommendation'])

            callType = recommendation['type']
            isBuy = recommendation["isBuy"]
            buyPrice = float(recommendation["buyPrice"])
            targetPrice = float(recommendation["targetPrice"])
            stopLoss = float(recommendation["stopLoss"])
            tag = recommendation['tag']
            risk = recommendation['risk']
            stockID = recommendation['stockID']
            usersList = recommendation['users']

            users = firestore_db.collection(u'users').document(u'customers').collection(u'users').get()

            possibleUsers = []
            possibleTokens = []

            allUsers = {}
            allUsersTokens = {}

            for user in users:
                userID = user.id
                userObj = user.to_dict()

                userContacts = firestore_db.collection(u'users').document(u'customers').collection(u'users').document(userID).collection(u'contacts').where('phoneNum', '==', phoneNum).get()

                print(userObj)

                if len(userContacts) > 0:
                    possibleUsers.append(userID)
                    print(userObj)
                    if 'token' in userObj:
                        possibleTokens.append(userObj['token'])

                allUsers[userID] = userObj['phoneNum']
                if 'token' in userObj:
                    allUsersTokens[userObj['phoneNum']] = userObj['token']

            print("IDENTIFYING ERROR")

            adminContacts = firestore_db.collection(u'users').document(u'admin').collection(u'users').document(uid).collection(u'contacts').get()
            adminContactsList = []
            for contact in adminContacts:
                contactObj = contact.to_dict()
                adminContactsList.append(contactObj['phoneNum'])
                if contactObj['phoneNum'] in allUsersTokens:
                    possibleTokens.append(allUsersTokens[contactObj['phoneNum']])

            possibleUsers = list(set(adminContactsList).union(set(possibleUsers)))

            print("IDENTIFYING ERROR 1")

            firestore_db.collection(u'recommended').document().set({
                "createdBy": uid,
                "buyPrice": buyPrice,
                "createdAt": SERVER_TIMESTAMP,
                "isBuy": isBuy,
                "risk": risk,
                "stockID": stockID,
                "stopLoss": stopLoss,
                "tag": tag,
                "targetPrice": targetPrice,
                "type": callType,
                "users": possibleUsers
            })

            print("IDENTIFYING ERROR 2")

            stockName = (firestore_db.collection(u'stocks').document(stockID).get()).to_dict()['name']

            print("IDENTIFYING ERROR 3")

            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title="New Recommendation!",
                    body="You have a new recommendation for {}".format(stockName)
                ),
                tokens=possibleTokens,
            )
            messaging.send_multicast(message)

            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def get_admin_orders(request):
    if request.method == "POST":
        try:
            phoneNum = request.POST['phoneNum']

            orders = firestore_db.collection(u'orders').where('admins', "array_contains", phoneNum).where(u'status', '==', "Ordered").get()

            ordersList = []

            for order in orders:
                orderObj = order.to_dict()
                orderObj['id'] = order.id

                stockID = orderObj['stockID']
                stockDetails = (firestore_db.collection(u'stocks').document(stockID).get()).to_dict()
                stockDetails['open'] = 180.1
                stockDetails['high'] = 185
                stockDetails['low'] = 178.5
                stockDetails['close'] = 184.74
                stockDetails['volume'] = 4032
                stockDetails['change'] = 3.11
                stockDetails['change_p'] = 1.7123

                orderObj['stock'] = stockDetails

                userID = orderObj['customerID']
                userDetails = firestore_db.collection(u'users').document(u'customers').collection(u'users').document(userID).get()
                if userDetails.exists:
                    userDetailsObj = userDetails.to_dict()
                    orderObj['customerName'] = userDetailsObj['name']
                    orderObj['customerPhoneNum'] = userDetailsObj['phoneNum']

                ordersList.append(orderObj)

            return Response(data={"result": "success", "orders": ordersList}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def get_executed_orders(request):
    if request.method == "POST":
        try:
            phoneNum = request.POST['phoneNum']

            orders = firestore_db.collection(u'orders').where('admins', "array_contains", phoneNum).where(u'status', '==', "Executed").get()

            ordersList = []

            for order in orders:
                orderObj = order.to_dict()
                orderObj['id'] = order.id

                stockID = orderObj['stockID']
                stockDetails = (firestore_db.collection(u'stocks').document(stockID).get()).to_dict()
                stockDetails['open'] = 180.1
                stockDetails['high'] = 185
                stockDetails['low'] = 178.5
                stockDetails['close'] = 184.74
                stockDetails['volume'] = 4032
                stockDetails['change'] = 3.11
                stockDetails['change_p'] = 1.7123

                userID = orderObj['customerID']
                userDetails = firestore_db.collection(u'users').document(u'customers').collection(u'users').document(userID).get()
                if userDetails.exists:
                    userDetailsObj = userDetails.to_dict()
                    orderObj['customerName'] = userDetailsObj['name']
                    orderObj['customerPhoneNum'] = userDetailsObj['phoneNum']

                orderObj['stock'] = stockDetails

                ordersList.append(orderObj)

            return Response(data={"result": "success", "orders": ordersList}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def update_orders_status(request):
    if request.method == "POST":
        try:
            orderIDs = json.loads(request.POST['orders'])
            
            batch = firestore_db.batch()
            for orderID in orderIDs:
                batch.update(firestore_db.collection(u'orders').document(orderID), {
                    u'status': 'Executed'
                })
            batch.commit()
            
            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

############################################
################# SESSION ##################
############################################

@api_view(['GET'])
def get_events(request):
    if request.method == "GET":
        try:
            isLoadExtra = False
            if "loadExtra" in request.GET:
                isLoadExtra = True

            events = firestore_db.collection(u'events').get()

            eventsList = []

            for event in events:
                eventObj = event.to_dict()
                eventObj['id'] = event.id
                eventObj['attendees'] = []

                if isLoadExtra:
                    attendees = firestore_db.collection(u'events').document(event.id).collection('attendees').get() 

                    for attendee in attendees:
                        attendeeObj = attendee.to_dict()
                        attendeeObj['id'] = attendee.id
                        eventObj['attendees'].append(attendeeObj)

                eventsList.append(eventObj)

            return Response(data={"result": "success", "events": eventsList}, status=200)

        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def register_for_event(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']
            eventID = request.POST['eventID']
            name = request.POST['name']
            phoneNum = request.POST['phoneNum']
            email = request.POST['email']

            firestore_db.collection(u'events').document(eventID).collection(u'attendees').document().set({
                "userID": uid,
                "name": name,
                "phoneNum": phoneNum,
                "email": email,
                "createdAt": SERVER_TIMESTAMP,
            })

            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def create_event(request):
    if request.method == "POST":
        try:
            description = request.POST['description']
            documentURL = request.POST['documentURL']
            price = float(request.POST['price'])

            firestore_db.collection(u'events').document().set({
                "description": description,
                "documentURL": documentURL,
                "price": price,
                "createdAt": SERVER_TIMESTAMP,
            })

            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['GET'])
def get_videos(request):
    if request.method == "GET":
        try:
            videos = firestore_db.collection(u'videos').get()

            videosList = []

            for video in videos:
                videoObj = video.to_dict()
                videoObj['id'] = video.id
                videosList.append(videoObj)

            return Response(data={"result": "success", "videos": videosList}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)
        
@api_view(['POST'])
def add_video(request):
    if request.method == "POST":
        try:
            videoURL = request.POST['videoURL']

            firestore_db.collection(u'videos').document().set({
                "url": videoURL,
                "createdAt": SERVER_TIMESTAMP,
            })

            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['GET'])
def get_blogs(request):
    if request.method == "GET":
        try:
            blogs = firestore_db.collection(u'blogs').get()

            blogsList = []

            for blog in blogs:
                blogsObj = blog.to_dict()
                blogsObj['id'] = blog.id
                blogsList.append(blogsObj)

            return Response(data={"result": "success", "blogs": blogsList}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def create_blog(request):
    if request.method == "POST":
        try:
            description = request.POST['description']
            documentURL = request.POST['documentURL']
            link = request.POST['link']

            firestore_db.collection(u'blogs').document().set({
                "description": description,
                "documentURL": documentURL,
                "link": link,
                "createdAt": SERVER_TIMESTAMP,
            })

            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

############################################
################## MISC ####################
############################################

@api_view(['POST'])
def get_contacts(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']

            contacts = firestore_db.collection(u'users').document(u'admin').collection(u'users').document(uid).collection(u'contacts').get()

            contactsList = []

            for contact in contacts:
                contactObj = contact.to_dict()
                
                contactsList.append(contactObj);                

            return Response(data={"result": "success", "contacts" : contactsList}, status=200)
            
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def sync_contacts(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']
            isAdmin = request.POST['userType'] == 'Admin'
            contacts = json.loads(request.POST['contacts'])

            existingPhoneNumbers = []
            adminExistingContacts = firestore_db.collection(u'users').document(u'admin' if isAdmin else u'customers').collection(u'users').document(uid).collection(u'contacts').get()
            for contact in adminExistingContacts:
                existingPhoneNumbers.append(contact['phoneNum'])

            existingPhoneNumbers = list(set(existingPhoneNumbers))

            users = firestore_db.collection(u'users').document(u'customers' if isAdmin else u'admin').collection(u'users').get()
            allUserPhoneNumbers = [user.to_dict()['phoneNum'] for user in users]

            batch = firestore_db.batch()
            for contact in contacts:
                if contact['phoneNum'] in allUserPhoneNumbers and not (contact['phoneNum'] in existingPhoneNumbers):
                    batch.set(firestore_db.collection(u'users').document(u'admin' if isAdmin else u'customers').collection(u'users').document(uid).collection(u'contacts').document(), contact)
            batch.commit()

            return Response(data={"result": "success"}, status=200)

        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def search(request):
    if request.method == "POST":
        try:
            queryTerm = request.POST['query'].lower()

            queriedStocks = firestore_db.collection('stocks').where(u'nameSmall', '>=', queryTerm).where(u'nameSmall', '<=', queryTerm + '\uf8ff').get()

            queriedStocksList = []

            for stock in queriedStocks:
                stockObj = stock.to_dict()

                stockObj['id'] = stock.id

                stockObj['open'] = 180.1
                stockObj['high'] = 185
                stockObj['low'] = 178.5
                stockObj['close'] = 184.74
                stockObj['volume'] = 4032
                stockObj['change'] = 3.11
                stockObj['change_p'] = 1.7123

                queriedStocksList.append(stockObj)

            return Response(data={"result": "success", "stocks" : queriedStocksList}, status=200)
            
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def get_notifications(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']
            isAdmin = request.POST['userType'] == 'Admin'
            
            notifications = firestore_db.collection(u'users').document(u'admin' if isAdmin else u'customers').collection(u'users').document(uid).collection(u'notifications').get()
            
            notificationsList = [notif.to_dict() for notif in notifications]

            return Response(data={"result": "success", "notifications": notificationsList}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def save_token(request):
    if request.method == "POST":
        try:
            uid = request.POST['uid']
            isAdmin = request.POST['userType'] == 'Admin'
            token = request.POST['token']

            print(uid);
            print(isAdmin);
            print(token);
            
            firestore_db.collection(u'users').document(u'admin' if isAdmin else u'customers').collection(u'users').document(uid).update({
                "token": token
            })

            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)

@api_view(['POST'])
def try_notif_sender(request):
    if request.method == "POST":
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title="Test",
                    body="This is a test notification"
                ),
                tokens=["duwBGnJZSVq_l58NKsblwg:APA91bE-_fJ3XIAQ6XN16TFFWmffsK0uhv5m87Echhhgu8lEHXf4rHC7xgtf2aOmrOrrUzyg8nn4PQXhNiOHl-ZwDWpGG8vP3vDZAuEoQ4nl1mZTJrtocQFOav53yPQSgOfOnKSZyikn"],
            )
            response = messaging.send_multicast(message)

            print('{0} messages were sent successfully'.format(response.success_count))

            return Response(data={"result": "success"}, status=200)
        except Exception as e:
            print(e)
            return Response(data={"result" : "failure"}, status=400)
    else:
        return Response(data={"result" : "failure"}, status=405)