import sys
import json

# Processors for various event types
# Receive json object in string form
# Process Method is passed to yajl helper to process streamed JSON
# Action method is called by the main script after collecting processing is complete
# Each processor has the events list for debugging. It can be removed later. 
# Do the jazz. 
class BaseProcessor:
	def __init__(self):
		self.writer = FileWriter()
		self.cnt = 0

	def process(self, js):
		try:
			obj = json.loads(js)
			target_event = obj['type'].strip()
	
			if target_event in Event.Events:
				#print("Processing %s" % target_event)
				processor = Event.Processors[target_event](self.writer)
				processor.process(obj)	
				processor.action()
				self.cnt+=1
			else:
				pass
		except:
			print("BaseProcessor ERROR: %s"%js)
			print(sys.exc_info())

	def action(self):
		print("Processed %d relevant events. Commiting changes."%self.cnt)
		self.writer.commit()

	def __exit__(self, type, value, traceback):
		self.action()

# Prints a given number of json objects of the given type from the stream
class DebugProcessor:
	def __init__(self, target_event, cnt=1):
		self.count=cnt
		self.target_event = target_event

	def process(self, js):
		try:
			obj = json.loads(js)
			
			if obj['type'] == self.target_event and self.count > 0:
				print(json.dumps(obj, sort_keys=True, indent=5))
				self.count -= 1

				if self.count > 0:
					print("************")
		except:
			print("DebugProcessor ERROR: %s"%js)
			print(sys.exc_info()[0])

	def action(self):
		pass

class FollowProcessor:
	def __init__(self, writer):
		self.follows = ()
		self.writer = writer

	def process(self, obj):
		try:
			user1 = obj["actor"]
			user2 =  obj["payload"]["target"]["login"]
			created_at = obj["created_at"]
			self.follows = (user1, user2, created_at)
		except:
			print("ERROR: %s"%str(obj))
			print(sys.exc_info())

	def action(self):
		# print self.follows
		self.writer.add_followers(self.follows)

class MemberProcessor:
	def __init__(self, writer):
		# User A listed User B as collaborator
		self.writer = writer

	def process(self, obj):
		try:
			self.member = obj['payload']['member']['login']
			self.repo = obj['repository']
			self.created_at = obj['created_at']
		except:
			print("ERROR: %s"%str(obj))
			print(sys.exc_info())

	def action(self):
		#print self.collab
		self.writer.add_collab(self.member, self.repo, self.created_at)	
		
class CreateProcessor: 
	def __init__(self, writer):		
		# User A created a repository
		self.writer = writer

	def process(self, obj):
		try:
			self.repo = obj['repository']
		except:
			print("ERROR: %s"%str(obj))
			print(sys.exc_info()[0])

	def action(self):
		self.writer.add_repo(self.repo)
			
class ForkProcessor:
	def __init__(self, writer):		
		# User A created a repository
		self.writer = writer

	def process(self, obj):
		try:
			self.userid = obj['actor']
			self.repo = obj['repository']
			self.created_at = obj['created_at']
		except:
			print("ERROR: %s"%str(obj))
			print(sys.exc_info()[0])

	def action(self):
		self.writer.add_fork(self.userid, self.repo, self.created_at)

class WatchProcessor:
	def __init__(self, writer):
		# User A created a repository
		self.writer = writer

	def process(self, obj):
		try:
			self.userid = obj['actor']
			self.repo = obj['repository']
			self.created_at = obj['created_at']
		except:
			print("ERROR: %s"%str(obj))
			print(sys.exc_info()[0])

	def action(self):
		self.writer.add_watch(self.userid, self.repo, self.created_at)

class IssuesProcessor:
	def __init__(self, writer):		
		# User A created a repository
		self.writer = writer

	def process(self, obj):
		try:
			self.userid = obj['actor']
			self.repo = obj['repository']
			self.created_at = obj['created_at']

		except:
			print("ERROR: %s"%str(obj))
			print(sys.exc_info()[0])

	def action(self):
		self.writer.add_issue(self.userid, self.repo, self.created_at)

class PullRequestProcessor:
	def __init__(self, writer):
		# User A created a repository
		self.writer = writer

	def process(self, obj):
		try:
			self.userid = obj['actor']
			self.repo = obj['repository']
			self.status = obj['payload']['action']
			self.created_at = obj['created_at']
		except:
			print("ERROR: %s"%str(obj))
			print(sys.exc_info()[0])

	def action(self):
		self.writer.add_pull(self.userid, self.repo, self.status, self.created_at)
###
### FileWriter class ###
###

class FileWriter:
	def __init__(self):
		self.files = {}

		for key, val in Event.Files.iteritems():
			self.files[key] = open(val, "a")	

	def tsv(self, tup, limit=None):
		s = ""
		
		if limit==None:
			limit = len(tup)

		for i in range(limit):
			s += tup[i]

			if i!=limit-1:
				s += "\t"	
			else:
				s += "\n"

		return s

	def commit(self):
		self.close()
	
	def close(self):
		for key, val in self.files.iteritems():
			self.files[key].close()

	def add_followers(self, follows):
		self.files[Event.FollowEvent].write(self.tsv(follows))

	def add_collab(self, userid, repo, created_at):
		row = (userid, repo["owner"], repo["name"], created_at) 
		self.files[Event.MemberEvent].write(self.tsv(row))		

	def add_repo(self, repo):
		language = repo['language'] if 'language' in repo else ""

		row = (repo['owner'], repo['name'], str(repo['watchers']), str(repo['forks']), language, repo['created_at'])
		self.files[Event.CreateEvent].write(self.tsv(row))

	def add_fork(self, userid, repo, created_at):
		row = (userid, repo["owner"], repo["name"], created_at)
		self.files[Event.ForkEvent].write(self.tsv(row))
	
	def add_watch(self, userid, repo, created_at):
		row = (userid, repo["owner"], repo["name"], created_at)
		self.files[Event.WatchEvent].write(self.tsv(row))
	
	def add_issue(self, userid, repo, created_at):
		row = (userid, repo["owner"], repo["name"], created_at)
		self.files[Event.IssuesEvent].write(self.tsv(row))

	def add_pull(self, userid, repo, status, created_at):
		row = (userid, repo["owner"], repo["name"], status, created_at)
		self.files[Event.IssuesEvent].write(self.tsv(row))

class Event:
	FollowEvent = 'FollowEvent'
	CreateEvent = 'CreateEvent'
	ForkEvent = 'ForkEvent'
	WatchEvent = 'WatchEvent'
	IssuesEvent = 'IssuesEvent'
	MemberEvent = 'MemberEvent'
	PullRequestEvent = 'PullRequestEvent'

	# Must be in sync with above variables	
	Events = [FollowEvent, CreateEvent, ForkEvent, WatchEvent, IssuesEvent, MemberEvent, PullRequestEvent]

	# Must be in sync with function definitions below
	Processors = {FollowEvent: FollowProcessor, CreateEvent: CreateProcessor, ForkEvent: ForkProcessor, WatchEvent: WatchProcessor, IssuesEvent: IssuesProcessor, MemberEvent: MemberProcessor, PullRequestEvent: PullRequestProcessor}

	Files = {FollowEvent: "followers.tsv", CreateEvent: "repo.tsv", ForkEvent: "fork.tsv", WatchEvent: "watch.tsv", IssuesEvent: "issues.tsv", MemberEvent: "collab.tsv", PullRequestEvent: "pull.tsv"}
