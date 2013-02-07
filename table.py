
import csv
import os
import condition
import string
import value
from operator import __and__
from value import Value
from xml.dom.minidom import parse

class Table:

	def __init__(self, filename=None, name=None):
		self.columns = []
		self.types = []
		self.data = []
		self.dumpcnt = 0
		self.name = None
		if not filename is None:
			self.load(filename)
		if not name is None:
			self.name = name

	def setColumnNames(self, columns):
		for col in columns:
			self.columns.append(col)

	def load(self, filename):
		"""
		Load data from either XML or TSV file
		"""
		f = open(filename, 'r')
		_,ext = os.path.splitext(filename);
		if ext=='.xml':
			# Parse the XML file
			dom = parse(f)
			f.close()
			self.name = dom.documentElement.tagName
			xmlrows = dom.getElementsByTagName('row')
			for xmlrow in xmlrows:
				attr = xmlrow.attributes
				for i in range(attr.length):
					name = attr.item(i).name
					if not name in self.columns:
						# Add column to the table
						elt = Value(attr.item(i).value)
						self.columns.append(name)
						self.types.append(elt.getType())
						for r in self.data:
							r.append(Value())
				row = []
				row = [xmlrow.getAttribute(name) for name in self.columns]
				self.addrow(row)
		else:
			# Assume the input is a TSV file
			data = csv.reader(f,delimiter='\t')
			init = True
			for row in data:
				if init:
					self.columns = ['']*len(row)
					self.types = [type(None)]*len(row)
					init = False
				self.addrow([cell.decode('unicode-escape') for cell in row])

	def addrow(self, strrow):
		assert len(strrow) == len(self.columns)
		row = []
		for i in range(len(strrow)):
			val = Value(strrow[i])
			#print str(val.getType())+' et '+str(self.types[i])
			if self.types[i] == type(None):
				# Initialize type
				self.types[i] = val.getType()
				row.append(val)
			elif val.getType() is self.types[i] or val.getType() is None:
				row.append(val)
			else:
				# Convert all other values in the column back to string
				# TODO : handle more fine-grained type fallback (eg Float to Int)
				row.append(Value(val=strrow[i]))
				for r in self.data:
					if not r[i].getType() is None:
						r[i] = Value(val=unicode(r[i]))
				self.types[i] = unicode
		self.data.append(row)

	def write(self, filename):
		"""
		Write the data to a TSV file
		"""
		f = open(filename,'wb')
		wr = csv.writer(f,delimiter='\t',quoting=csv.QUOTE_ALL)
		for row in self.data:
			strrow = []
			for cell in row:
				strrow.append(unicode(cell).encode('unicode-escape'))
			wr.writerow(strrow)
		f.close()

	def dump(self,n=float('inf'),reset=False):
		"""
		Dumps n rows of the table to console.
		If reset=True, the dump starts over from the 1st row
		"""
		if reset:
			self.dumpcnt = 0
		colwidth = 17
		join = lambda l: '| '+' | '.join(l)+' |'
		dump = join([string.center(name[:colwidth],colwidth) for name in self.columns])
		sep = '+'*len(dump)
		dump = sep+'\n'+dump+'\n'+sep
		for i in [x+self.dumpcnt for x in range(n)]:
			if i >= len(self.data):
				break
			dump += '\n'+join([string.ljust(str(val)[:colwidth],colwidth) for val in self.data[i]])
			self.dumpcnt += 1
		dump += '\n'+sep
		print dump

	def name(self):
		return self.name

	def getRow(self, i):
		return self.data[i]

	def getColumn(self, j):
		return [row[j] for row in self.data]

	def newTable(self):
		table = Table(name=self.name)
		table.columns = self.columns
		table.types = self.types
		return table

	def getTuples(self, condition, col):
		table = self.newTable()
		f = lambda row: reduce(__and__,[c.eval(row[col]) for c in condition])
		try:
			table.data = filter(f,self.data)
		except TypeError:
			table.data = filter(lambda row:condition.eval(row[col]),self.data)
		return table

	def aggregate(self, attributes, col, aggregator):
		
		if not len(self.data):
			return []
		row = self.data[0]
		row[col] = aggregator.calc(self.getColumn(col))
		return row

	def getColumns(self, columns):
		table = Table(name=self.name)
		table.columns = [self.columns[i] for i in columns]
		table.types = [self.types[i] for i in columns]
		for row in self.data:
			table.data.append([row[i] for i in columns])
		return table