from __future__ import print_function
import httplib2, os, base64, re

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'eBay Sales Counter'
Unparsed = 'Label_27' #Put the label of your "Item Sold" messages here.

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def ListMessagesWithLabels(service, user_id, label_ids=[]):
    """List all Messages of the user's mailbox with label_ids applied.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      label_ids: Only return Messages with these labelIds applied.

    Returns:
      List of Messages that have all required Labels applied. Note that the
      returned list contains Message IDs, you must use get with the
      appropriate id to get the details of a Message.
    """
    try:
        response = service.users().messages().list(userId=user_id, labelIds=label_ids).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, labelIds=label_ids,
                                                       pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except (errors.HttpError, error):
        print('An error occurred: %s' % error)


def ReturnMessageBody(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, ).execute()
        bodyunconverted = message['payload']['parts'][0]['body']['data']
        body = base64.urlsafe_b64decode(bodyunconverted.encode('ASCII'))
        #body = base64.urlSafeBase64Decode(bodyunconverted)
        #print (body)
        return body

    except (errors.HttpError, error):
        print('An error occurred: %s' % error)


def GetQuantitySold(message):
    QuantitySold = re.search('(?<=Quantity Sold: )(\d*)', message.decode())
    #print (message)
    return int(QuantitySold.group())

def GetItemName(message):
    ItemName = re.search('(?<=.jpg" alt=")(.*)(?=" class="product-image")', message.decode())
    return ItemName.group(0)


def PrintDict(dictionary):
    for item in sorted(dictionary):
        print("Item: %s \n Sold: %s" % (item, dictionary[item]))


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    gmail_service = discovery.build('gmail', 'v1', http=http)

    messageList = ListMessagesWithLabels(gmail_service, 'me', Unparsed)
    # Retrieve a list with IDs of all messages using unparsed Label


    sold = {}

    count = -1
    print("Beginning Operation...")
    print("...")

    for message in messageList:
        count += 1

        message = ReturnMessageBody(gmail_service, 'me', messageList[count]['id'])

        QuantitySold = GetQuantitySold(message)

        ItemName = GetItemName(message)

        if ItemName in sold:
            sold[ItemName] += QuantitySold
            print("%s exists! Adding %s." % (ItemName, QuantitySold))
        else:
            sold[ItemName] = QuantitySold
            print("%s does not exist! Creating and adding %s." % (ItemName, QuantitySold))
    print("...")
    print("...")
    print("Operation Complete")

    print("\n \n \nPrinting out totals")

    PrintDict(sold)
    input('Press ENTER to exit')

if __name__ == '__main__':
    main()
