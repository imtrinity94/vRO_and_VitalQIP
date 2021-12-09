#!/usr/bin/env python
import argparse
import re
import uuid
import sys

from xml.dom import minidom
from xml.parsers.expat import ExpatError

try:
    from urllib.request import Request, urlopen, HTTPError, URLError  # Python 3
except:
    from urllib2 import Request, urlopen, HTTPError, URLError  # Python 2


def message_id():
    return uuid.uuid4().__str__().replace('-', '')[:31]


def headers(soap_action):
    return  {'Content-Type': 'text/xml; charset=utf-8', 'SOAPAction': soap_action}


def pretty_xml(doc):
    try:
        return minidom.parseString(doc).toprettyxml()
    except ExpatError:
        return doc


#
# Script arguments
#
parser = argparse.ArgumentParser()
parser.add_argument('--hostname', help='Fully qualified hostname including http. Eg: http://someqipserver.acme.com')
parser.add_argument('--port', help='TCP/IP port on which the VitalQIP web server is configured to listen. The default value is 80.', default='80')
parser.add_argument('--username', help='QIP username')
parser.add_argument('--password', help='QIP password')
parser.add_argument('--organization', help='QIP users organization')
parser.add_argument('--node-hostname', help='Hostname of the node you are provisioning')
parser.add_argument('--node-class', help='QIP node class')
parser.add_argument('--subnet', help='The subnet to request an IP Address from. Eg: 192.168.0.0')
args = parser.parse_args()

#
# Variables
#
IP_ADDRESS_REGEX = re.compile('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
RESULT_REGEX = re.compile('<.+result>(\w+)</.+result>')
URL_ENDPOINT='{0}:{1}/ws/services/VQIPWebService'.format(args.hostname, args.port)
LOCALE = 'en_US'
USERNAME=args.username
PASSWORD=args.password
ORGANIZATION=args.organization
HOSTNAME=args.node_hostname
NODE_CLASS=args.node_class
SUBNET=args.subnet
IP_ADDRESS=None

#
# SOAP header XML template
#
# Description: Main structure of the SOAP request
#   Page name: Incoming/outgoing message structure format
#   Page num#: 2-6
#
xml_soap_template = '''<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsa="http://www.w3.org/2005/08/addressing">
<soapenv:Header>
  <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
    <wsse:UsernameToken>
      <wsse:Username>{USERNAME}</wsse:Username>
      <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{PASSWORD}</wsse:Password>
    </wsse:UsernameToken>
  </wsse:Security>
  <wsa:To>{URL_ENDPOINT}</wsa:To>
  <wsa:MessageID>urn:uuid:{MESSAGE_ID}</wsa:MessageID>
  <wsa:Action>{ACTION}</wsa:Action>
</soapenv:Header>
<soapenv:Body>
  <ns1:{REQ_TYPE} xmlns:ns1="http://alcatel-lucent.com/qip/nb/ws" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="ns1:{REQ_TYPE}">
    <ns1:commonParam>
      <ns1:organization>{ORGANIZATION}</ns1:organization>
      <ns1:locale>{LOCALE}</ns1:locale>
    </ns1:commonParam>
    {BODY}
  </ns1:{REQ_TYPE}>
</soapenv:Body>
</soapenv:Envelope>
'''

#
# Get a IPv4 address by hostname XML template
#
# Description: An object represents an IPv4 address
#   Page name: V4 address
#   Page num#: 2-264
#
xml_ipv4_address_get = '''
    <ns1:reqObject xsi:type="ns1:V4_ADDR_REC">
      <ns1:objectAddr></ns1:objectAddr>
      <ns1:subnetAddr></ns1:subnetAddr>
      <ns1:objectName>{OBJECT_NAME}</ns1:objectName>
      <ns1:objectClass></ns1:objectClass>
    </ns1:reqObject>
'''

#
# Get IPv4 address request XML template
#
# Description: Retrieves the next free IP address within a subnet and marks the address as "selected"
#   Page name: V4 get IP address
#   Page num#: 2-280
#
xml_ipv4_address_get_request = '''
    <ns1:reqObject xsi:type="ns1:V4_GET_IP_ADDRESS_REC">
      <ns1:ipAddrStr>{SUBNET}</ns1:ipAddrStr>
    </ns1:reqObject>
'''

#
# Update a IPv4 address XML template
#
# Description: An object represents an IPv4 address
#   Page name: V4 address
#   Page num#: 2-264
#
xml_ipv4_address_modify = '''
    <ns1:reqObject xsi:type="ns1:V4_ADDR_REC">
      <ns1:objectAddr>{IP_ADDRESS}</ns1:objectAddr>
      <ns1:subnetAddr>{SUBNET}</ns1:subnetAddr>
      <ns1:objectName>{OBJECT_NAME}</ns1:objectName>
      <ns1:objectClass>{OBJECT_CLASS}</ns1:objectClass>
      <ns1:domainName/>
      <ns1:expiredDate/>
      <ns1:applName/>
      <ns1:manufacturer/>
      <ns1:modelType/>
      <ns1:purchaseDate/>
      <ns1:locationId>0</ns1:locationId>
      <ns1:street1/>
      <ns1:street2/>
      <ns1:city/>
      <ns1:state/>
      <ns1:zip/>
      <ns1:country/>
      <ns1:contactId>0</ns1:contactId>
      <ns1:contactLastName/>
      <ns1:contactFirstName/>
      <ns1:contactEmail/>
      <ns1:contactPhone/>
      <ns1:contactPager/>
      <ns1:dynamicConfig>Static</ns1:dynamicConfig>
      <ns1:hardwareType>None</ns1:hardwareType>
      <ns1:mailForwarders/>
      <ns1:mailHosts/>
      <ns1:hubSlots/>
      <ns1:dnsServers/>
      <ns1:timeServers/>
      <ns1:defaultRouters/>
      <ns1:userClasses/>
      <ns1:users/>
      <ns1:nameService>A,PTR</ns1:nameService>
      <ns1:dhcpServer/>
      <ns1:dhcpOptionTemplate/>
      <ns1:dhcpPolicyTemplate/>
      <ns1:leaseTime>-1</ns1:leaseTime>
      <ns1:ttlTime>-1</ns1:ttlTime>
      <ns1:vendorClass/>
      <ns1:dualProtocol/>
      <ns1:allowModifyDynamicRRs>False</ns1:allowModifyDynamicRRs>
      <ns1:tombstoned>0</ns1:tombstoned>
      <ns1:externalComment/>
      <ns1:externalTimestamp/>
      <ns1:manual_flag>0</ns1:manual_flag>
      <ns1:nodeId>0</ns1:nodeId>
      <ns1:uniqueNodeId/>
      <ns1:aTTL>-1</ns1:aTTL>
      <ns1:ptrTTL>-1</ns1:ptrTTL>
      <ns1:publishA>Always</ns1:publishA>
      <ns1:publishPTR>Always</ns1:publishPTR>
    </ns1:reqObject>
'''


#
# Check if hostname exists
#
# XML data to get an IPv4 Address
data = xml_soap_template.format(
    USERNAME=USERNAME,
    PASSWORD=PASSWORD,
    URL_ENDPOINT=URL_ENDPOINT,
    MESSAGE_ID=message_id(),
    ACTION='VQIPManager_GetRequest',
    REQ_TYPE='GetRequest',
    ORGANIZATION=ORGANIZATION,
    LOCALE=LOCALE,
    BODY=xml_ipv4_address_get.format(
        OBJECT_NAME=HOSTNAME
    )
)

# If hostname does not exist API will send HTTP 500 error with WS_OBJECT_NAME_NOT_FOUND in response message
try:
    request = Request(URL_ENDPOINT, data=data, headers=headers('VQIPManager_GetRequest'))
    response = urlopen(request).read()
    print 'Step: Hostname check\nStatus: Failed\nReason: Hostname already exists!\n'
    sys.exit(1)
except HTTPError as e:
    message = e.read()
    if not 'WS_OBJECT_NAME_NOT_FOUND' in message:
        print 'Step: Hostname check\nStatus: Failed\nReason:\n{0}\n'.format(pretty_xml(message))
        sys.exit(1)

#
# Reserve IP address
#
# XML data to get an IPv4 Address
data = xml_soap_template.format(
    USERNAME=USERNAME,
    PASSWORD=PASSWORD,
    URL_ENDPOINT=URL_ENDPOINT,
    MESSAGE_ID=message_id(),
    ACTION='VQIPManager_GetRequest',
    REQ_TYPE='GetRequest',
    ORGANIZATION=ORGANIZATION,
    LOCALE=LOCALE,
    BODY=xml_ipv4_address_get_request.format(
        SUBNET=SUBNET
    )
)

# Request an IP address if it fails exit non-zero
try:
    request = Request(URL_ENDPOINT, data=data, headers=headers('VQIPManager_GetRequest'))
    response = urlopen(request).read()
except HTTPError as e:
    message = e.read()
    print 'Step: Requesting IP address\nStatus: Failed\nReason:\n{0}\n'.format(pretty_xml(message))
    sys.exit(1)

# Validate response
if RESULT_REGEX.search(response).group(1) != 'SUCCESS':
    print 'Step: Requesting IP address\nStatus: Failed\nReason:\n{0}\n'.format(pretty_xml(response))
    sys.exit(1)

# Search response body for IP address
IP_ADDRESS = IP_ADDRESS_REGEX.search(response).group(1)

#
# Update IPv4 address object information
#
# XML data to create node and assign IPv4 address
data = xml_soap_template.format(
    USERNAME=USERNAME,
    PASSWORD=PASSWORD,
    URL_ENDPOINT=URL_ENDPOINT,
    MESSAGE_ID=message_id(),
    ACTION='VQIPManager_UpdateRequest',
    REQ_TYPE='UpdateRequest',
    ORGANIZATION=ORGANIZATION,
    LOCALE=LOCALE,
    BODY=xml_ipv4_address_modify.format(
        IP_ADDRESS=IP_ADDRESS,
        SUBNET=SUBNET,
        OBJECT_NAME=HOSTNAME,
        OBJECT_CLASS=NODE_CLASS
    )
)

# Set IPv4 address object name and object class
try:
    request = Request(URL_ENDPOINT, data=data, headers=headers('VQIPManager_UpdateRequest'))
    response = urlopen(request).read()
except HTTPError as e:
    message = e.read()
    print 'Step: Update IPv4 address object\nStatus: Failed\nReason:\n{0}\n'.format(pretty_xml(message))
    sys.exit(1)

# Validate response
if RESULT_REGEX.search(response).group(1) != 'SUCCESS':
    print 'Step: Update IPv4 address object\nStatus: Failed\nReason:\n{0}\n'.format(pretty_xml(response))
    sys.exit(1)

print IP_ADDRESS
sys.exit(0)