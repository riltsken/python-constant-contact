import urllib2
import copy
import httplib

#open source lib http://code.google.com/p/httplib2/
#used for setting credentials,establishing connection,pulling xml
import httplib2

#open source lib http://code.google.com/p/feedparser/
#used for parsing the xml and returning it in a usuable format
import feedparser as fp

constantcontact_url = "https://api.constantcontact.com/ws/customers"
GET = "GET"
PUT = "PUT"
POST = "POST"

class ConstantContactException(httplib.HTTPException):

	def __init__(self,status,response_body,body=None):
		self.status = status
		self.response_body = response_body
		self.body = body

	def __str__(self):
		return repr(self.response_body)

class HTTPBadRequest(ConstantContactException):
	pass
class HTTPUnauthorized(ConstantContactException):
	pass
class HTTPNotFound(ConstantContactException):
	pass
class HTTPConflict(ConstantContactException):
	pass
class HTTPUnsupportedType(ConstantContactException):
	pass
class HTTPServerError(ConstantContactException):
	pass

EXCEPTION = {
	httplib.BAD_REQUEST: HTTPBadRequest,
	httplib.UNAUTHORIZED: HTTPUnauthorized,
	httplib.NOT_FOUND: HTTPNotFound,
	httplib.CONFLICT: HTTPConflict,
	httplib.UNSUPPORTED_MEDIA_TYPE: HTTPUnsupportedType,
	httplib.INTERNAL_SERVER_ERROR: HTTPServerError
}

def check_status_codes(response,response_body,body):
	try:
		raise EXCEPTION[int(response['status'])](response,response_body,body)
	except KeyError:
		pass

class Api(object):

	def __init__(self,api_key=None,username=None,password=None):

		self._api_key = api_key
		self._username = username
		self._password = password
		self._urllib2 = urllib2
		self._login = "%".join([api_key,username])
		self._establish_connection()

		self.contacts_url = "%s/%s/contacts" % (constantcontact_url, self._username)
		self.collections_url = "%s/%s/lists" % (constantcontact_url, self._username)

	def get_collection(self):

		header, xmlbody = self._request(self.collections_url)
		return fp.parse(xmlbody)
	
	def get_contact_list(self):

		header, xmlbody = self._request(self.contacts_url)
		return fp.parse(xmlbody)


	# I give two methods here, email or id, because sometimes we don't store the contact id, but we most definitely do the email
	# so it is a convenience to grab a contact by email.
	#
	# There is also a raw option, where it doesn't get parsed by feedparser. This is so you can easily return an updated entry without having to rebuild
	# the xml from scratch. Might have to make an xml rebuilder though for other parts of the api.

	def get_contact_by_email(self,email,raw=False):
	
		xmlstream = self._request('%s?email='.join([self.contacts_url,email.replace('@', '%40').lower()]))
		treequery = fp.parse(xmlstream[1])
		id = treequery['entries'][0]['id'].rsplit('/', 1)[1]
		if raw:
			return (id, self._request('%s/%s' % (self.contacts_url,id))[1])
		return (id, fp.parse(self._request('%s/%s' % (self.contacts_url,id))[1]))

	def get_contact_by_id(self,id,raw=False):

		if raw:
			return self._request('%s/%s' % (self.contacts_url,id))[1]
		return fp.parse(self._request('%s/%s' % (self.contacts_url,id))[1])
		
	def add_contact_to_lists_by_email(self,email,group_ids):

		id, contact = self.get_contact_by_email(email, raw=True)
		url = "%s/%s" % (self.contacts_url, id)
		body = self._add_to_contact_lists(contact,group_ids)
		return self._request(url=url,method=PUT,body=body)

	def add_contact_to_lists_by_id(self,id,group_ids):

		url = self.contacts_url
		body = self.contact_lists_template(email,group_ids,first_name,last_name) 
		return self._request(url=url,method=PUT,body=body)
		
	def create_contact_template(self,email,group_ids,first_name,last_name):

		contact_groups = ['<ContactList id="http://api.constantcontact.com/ws/customers/%s/lists/%s" />' % (self._username, id) for id in group_ids]

		entry_begin = '<entry xmlns="http://www.w3.org/2005/Atom">'
		title = '<title type="text"> </title>'
		updated = '<updated>2008-07-23T14:21:06.407Z</updated>'
		author = '<author></author>'
		id = '<id>data:,none</id>'
		summary = '<summary type="text">Contact</summary>'
		content_begin = '<content type="application/vnd.ctct+xml"><Contact xmlns="http://ws.constantcontact.com/ns/1.0/">'
		email = '<EmailAddress>%s</EmailAddress>' % email
		first_name = '<FirstName>%s</FirstName>' % first_name
		last_name = '<LastName>%s</LastName>' % last_name
		optin = '<OptInSource>ACTION_BY_CUSTOMER</OptInSource>'
		groups = '<ContactLists>\n%s</ContactLists>' % '\n'.join(contact_groups)
		content_end='</Contact></content>'
		entry_end = '</entry>'
		return ''.join([entry_begin, title, updated, author, id, summary, content_begin, \
			email, first_name, last_name, optin, groups, content_end, entry_end])

	def create_contact(self,email,group_ids,first_name='',last_name=''):

		url = self.contacts_url
		body = self.create_contact_template(email,group_ids,first_name,last_name) 
		response, body = self._request(url=url,method=POST,body=body)
		return (response,body)
	
	# This removes the contact from all the contact lists, this is not meant to be permanent or for the do-not-mail list
	def remove_contact_by_email(self,email):

		id, contact = self.get_contact_by_email(email,raw=True)
		fixed_body = self._remove_from_contact_lists(contact)
		return self._request("%s/%s" % (self.contacts_url, id), PUT, body=fixed_body)

	def remove_contact_by_id(self,id):

		id, contact = self.get_contact_by_id(id)
		fixed_body = self._remove_from_contact_lists(contact)
		return self._request("%s/%s" % (self.contacts_url, id), PUT, body=fixed_body)

	# Easiest way I could think of for managing the contact lists, it basically just removes all the whitespace to create one long string
	# where we split the part we want to mess around with (contactlist)
	def _remove_from_contact_lists(self,contact):

		contact = "".join([c.lstrip() for c in contact.split('\n')])
		if 'ContactLists' in contact:
			first = contact.split("<ContactLists>")[0]
			second = contact.split("</ContactLists>")[1]
			return "".join([first,second])
		return contact
		
	def _add_to_contact_lists(self,contact,group_ids=[]):
		
		contact = "".join([c.lstrip() for c in contact.split('\n')])
		contact_groups = ['<ContactList id="http://api.constantcontact.com/ws/customers/%s/lists/%s" />' % (self._username, id) for id in group_ids]
		
		if contact_groups:
			contact = self._remove_from_contact_lists(contact)
			if "<ContactLists>" in contact:
				split = "<ContactLists>"
				split_end = "</ContactLists>"
				second = "".join(contact_groups)
				first = contact.split(split)[0]
				third = contact.split(split_end)[1]
				return "".join([first,second,third])
			else:
				split = "</EmailAddress>"
				optinsource = "<OptInSource>ACTION_BY_CUSTOMER</OptInSource>"
				second = "".join([optinsource,"<ContactLists>","".join(contact_groups),"</ContactLists>"])
				first = contact.split(split)[0]
				first = "".join([first,"</EmailAddress>"])
				third = contact.split(split)[1]
				third.replace("</EmailAddress>", "")
				return "".join([first,second,third])

		return contact
		
	# We can use the same connection for multiple requests
	# possibility it times out but we'll see.
	def _request(self,url,method=GET,body=None,headers=None):

		headers = headers or {}
		# as far as I know, GET is the only one who doesn't use the alternate content-type and appended body
		if method == GET:
			response, response_body = self._connection.request(url,method,headers=headers)
		else:
			headers['Content-type'] = "application/atom+xml"
			response, response_body = self._connection.request(url,method,headers=headers,body=body)

		check_status_codes(response, response_body, body)
		return (response, response_body)
	
	def _establish_connection(self):

		self._connection = httplib2.Http()
		self._connection.add_credentials(self._login, self._password)
	
