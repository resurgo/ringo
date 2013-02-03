
import csv
import os
import time
from xml.dom.minidom import parse
import condition

class Table:

	def __init__(self, name):
		self.name = name
		self.columns = []
		self.types = []
		self.data = []

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
			xmlrows = dom.getElementsByTagName('row')
			for xmlrow in xmlrows:
				attr = xmlrow.attributes
				for i in range(attr.length):
					name = attr.item(i).name
					if not name in self.columns:
						# Add column to the table
						elt = Table.str2elt(attr.item(i).value)
						self.columns.append(name)
						self.types.append(type(elt))
						for r in self.data:
							r.append(None)
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
			e = Table.str2elt(strrow[i])
			if self.types[i] == type(None):
				# Initialize type
				self.types[i] = type(e)
				row.append(e)
			elif type(e) is self.types[i] or e is None:
				row.append(e)
			else:
				# Convert all other values in the column back to string
				row.append(strrow[i])
				for r in self.data:
					if not r[i] is None:
						r[i] = unicode(r[i])
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
				strrow.append(Table.elt2str(cell))
			wr.writerow(strrow)
		f.close()

	def name(self):
		return self.name

	def ithrow(self, data, i):
		return data[i]

	def jthcolumn(self, data, j):
		result = {}
		for row in data:
			result.add(row[j])

		return result

	def getTuples(self, conditions, col):
		result = []
		# apply all conditions
		for row in self.data:
			if condition.eval(row[col]):
				result.add(row)

		return result

	@staticmethod
	def str2elt(s):
		if s == '':
			return None
		try:
			return float(s)
		except ValueError:
			try:
				# TODO: use datetime module to keep milliseconds
				spl = s.split('.')
				return time.strptime(spl[0],'%Y-%m-%dT%H:%M:%S')
			except ValueError:
				return s

	@staticmethod
	def elt2str(e):
		if e is None:
			return ''
		elif type(e) is time.struct_time:
			return time.strftime('%Y-%m-%dT%H:%M:%S',e)
		else:
			return unicode(e).encode('unicode-escape')
